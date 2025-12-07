"""
Main Flask application entry point
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
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
            # Check Redis connection
            cache_service.ping()
            
            # Check vector service
            vector_service.get_stats()
            
            return jsonify({
                'status': 'healthy',
                'timestamp': metrics_collector.get_current_timestamp(),
                'version': '1.0.0'
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
            data = request.get_json()
            
            if not data or 'query' not in data:
                return jsonify({'error': 'Query is required'}), 400
            
            query = data['query']
            max_length = data.get('max_length', 500)
            temperature = data.get('temperature', app.config['OPENAI_TEMPERATURE'])
            
            # Generate content with RAG
            result = content_generator.generate_with_rag(
                query=query,
                max_length=max_length,
                temperature=temperature
            )
            
            # Record metrics
            response_time = metrics_collector.end_timer(start_time)
            metrics_collector.record_request('generate', response_time, True)
            
            return jsonify({
                'content': result['content'],
                'sources': result['sources'],
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
            data = request.get_json()
            
            if not data or 'query' not in data:
                return jsonify({'error': 'Query is required'}), 400
            
            query = data['query']
            limit = data.get('limit', app.config['MAX_SEARCH_RESULTS'])
            
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
        start_time = metrics_collector.start_timer()
        
        try:
            data = request.get_json()
            
            if not data or 'documents' not in data:
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

if __name__ == '__main__':
    # Get configuration from environment
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)
    
    # Run the application
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )