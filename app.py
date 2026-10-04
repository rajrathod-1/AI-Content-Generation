"""
Main Flask application entry point
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
import hmac
import logging
import os
import sys

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.config import config
from src.services.openai_service import OpenAIService
from src.services.vector_service import VectorService
from src.services.cache_service import CacheService
from src.services.content_generator import ContentGenerator
from src.utils.logger import setup_logger
from src.utils.metrics import MetricsCollector

MAX_QUERY_CHARS = 2000
SOURCE_FIELDS = ('title', 'url', 'snippet', 'score', 'source_type')


def clamp(value, low, high, default):
    """Coerce a client-supplied number into [low, high]."""
    try:
        return min(max(type(default)(value), low), high)
    except (TypeError, ValueError):
        return default


def read_query(data):
    """Return (query, error) from a JSON body."""
    query = data.get('query') if isinstance(data, dict) else None
    if not isinstance(query, str) or not query.strip():
        return None, 'Query is required'
    if len(query) > MAX_QUERY_CHARS:
        return None, f'Query must be at most {MAX_QUERY_CHARS} characters'
    return query.strip(), None

def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Enable CORS
    CORS(app)
    
    # Setup logging
    setup_logger(app.config['LOG_LEVEL'], app.config['LOG_FILE'])
    logger = logging.getLogger(__name__)
    
    # Initialize services
    cache_service = CacheService(app.config)
    openai_service = OpenAIService(app.config)
    vector_service = VectorService(app.config)
    content_generator = ContentGenerator(openai_service, vector_service, cache_service)
    metrics_collector = MetricsCollector()
    
    @app.route('/')
    def index():
        """Welcome page with API documentation"""
        return jsonify({
            'service': 'AI Content Generation Service',
            'version': '1.0.0',
            'status': 'running',
            'endpoints': {
                'health': '/api/health',
                'generate': 'POST /api/generate',
                'search': 'POST /api/search',
                'ingest': 'POST /api/ingest',
                'metrics': '/api/metrics'
            },
            'docs': 'See API_DOCUMENTATION.md for details'
        }), 200
    
    @app.route('/favicon.ico')
    def favicon():
        """Handle favicon requests"""
        return '', 204
    
    @app.route('/api/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            return jsonify({
                'status': 'healthy',
                'timestamp': metrics_collector.get_current_timestamp(),
                'version': '2.0.0',
                'cache': cache_service.ping(),
                'documents': vector_service.get_stats()['total_documents']
            }), 200
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return jsonify({
                'status': 'unhealthy',
                'error': str(e)
            }), 500
    
    @app.route('/api/generate', methods=['POST'])
    def generate_content():
        """Generate content using RAG"""
        start_time = metrics_collector.start_timer()
        
        try:
            data = request.get_json(silent=True)
            query, error = read_query(data)
            if error:
                return jsonify({'error': error}), 400
            
            # Clamp so a client can't run up the OpenAI bill
            max_length = clamp(data.get('max_length'), 50, 1500, 500)
            temperature = clamp(data.get('temperature'), 0.0, 1.5, app.config['OPENAI_TEMPERATURE'])
            
            # Generate content with RAG
            result = content_generator.generate_with_rag(
                query=query,
                max_length=max_length,
                temperature=temperature
            )
            
            # Record metrics
            response_time = metrics_collector.end_timer(start_time)
            metrics_collector.record_request(
                'generate', response_time, True,
                tokens_used=result.get('tokens_used', 0),
                cache_hit=result.get('cached', False)
            )
            
            return jsonify({
                'content': result['content'],
                # Sources carry full scraped page text internally; the client only needs these fields
                'sources': [{k: s.get(k) for k in SOURCE_FIELDS} for s in result['sources']],
                'cached': result.get('cached', False),
                'used_rag': result.get('used_rag', True),
                'model': result.get('model_used'),
                'response_time_ms': response_time,
                'timestamp': metrics_collector.get_current_timestamp()
            }), 200
            
        except Exception as e:
            response_time = metrics_collector.end_timer(start_time)
            metrics_collector.record_request('generate', response_time, False)
            logger.error(f"Content generation failed: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/search', methods=['POST'])
    def semantic_search():
        """Perform semantic search"""
        start_time = metrics_collector.start_timer()
        
        try:
            data = request.get_json(silent=True)
            query, error = read_query(data)
            if error:
                return jsonify({'error': error}), 400
            
            limit = clamp(data.get('limit'), 1, 20, app.config['MAX_SEARCH_RESULTS'])
            
            # Perform search
            results = vector_service.search(query, limit)
            
            # Record metrics
            response_time = metrics_collector.end_timer(start_time)
            metrics_collector.record_request('search', response_time, True)
            
            return jsonify({
                'results': results,
                'count': len(results),
                'response_time_ms': response_time,
                'timestamp': metrics_collector.get_current_timestamp()
            }), 200
            
        except Exception as e:
            response_time = metrics_collector.end_timer(start_time)
            metrics_collector.record_request('search', response_time, False)
            logger.error(f"Search failed: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/ingest', methods=['POST'])
    def ingest_documents():
        """Ingest new documents into the knowledge base"""
        # Writes to the shared index, so require a key; disabled when INGEST_API_KEY is unset
        expected = os.getenv('INGEST_API_KEY')
        provided = request.headers.get('X-API-Key', '')
        if not expected or not hmac.compare_digest(provided, expected):
            return jsonify({'error': 'Unauthorized'}), 401
        
        start_time = metrics_collector.start_timer()
        
        try:
            data = request.get_json(silent=True)
            
            if not data or not isinstance(data.get('documents'), list):
                return jsonify({'error': 'Documents are required'}), 400
            
            documents = data['documents']
            
            # Process and add documents
            processed_count = vector_service.add_documents(documents)
            
            # Record metrics
            response_time = metrics_collector.end_timer(start_time)
            metrics_collector.record_request('ingest', response_time, True)
            
            return jsonify({
                'processed_count': processed_count,
                'response_time_ms': response_time,
                'timestamp': metrics_collector.get_current_timestamp()
            }), 200
            
        except Exception as e:
            response_time = metrics_collector.end_timer(start_time)
            metrics_collector.record_request('ingest', response_time, False)
            logger.error(f"Document ingestion failed: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/api/metrics', methods=['GET'])
    def get_metrics():
        """Get system metrics"""
        try:
            metrics = metrics_collector.get_metrics()
            return jsonify(metrics), 200
        except Exception as e:
            logger.error(f"Metrics retrieval failed: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

# Create the application instance for Gunicorn
app = create_app(os.getenv('FLASK_ENV', 'production'))

if __name__ == '__main__':
    # Run the application
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )