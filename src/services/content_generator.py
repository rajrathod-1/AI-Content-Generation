"""
Content Generator service that combines RAG with OpenAI GPT-4
Integrates semantic search with content generation for high-quality responses
NOW INCLUDES REAL-TIME WEB SEARCH
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import hashlib

from .openai_service import OpenAIService, GenerationResult
from .vector_service import VectorService, SearchResult
from .cache_service import CacheService
from .realtime_search import RealTimeWebSearcher
from .query_classifier import QueryClassifier, QueryType

@dataclass
class RAGResult:
    """Result from RAG content generation"""
    content: str
    sources: List[Dict]
    query: str
    tokens_used: int
    response_time: float
    search_time: float
    generation_time: float
    cached: bool

class ContentGenerator:
    """High-level content generation service with RAG capabilities and real-time web search"""
    
    def __init__(self, openai_service: OpenAIService, vector_service: VectorService, cache_service: CacheService):
        self.openai_service = openai_service
        self.vector_service = vector_service
        self.cache_service = cache_service
        self.logger = logging.getLogger(__name__)
        
        # Initialize real-time web search
        self.web_searcher = RealTimeWebSearcher()
        
        # Initialize query classifier
        self.query_classifier = QueryClassifier()
        
        # Configuration
        self.max_context_length = 4000  # tokens
        self.relevance_threshold = 0.7
        self.min_search_results = 3
        
        # Statistics
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'average_response_time': 0.0,
            'average_search_time': 0.0,
            'average_generation_time': 0.0
        }
    
    def generate_with_rag(
        self,
        query: str,
        max_length: int = 500,
        temperature: float = 0.7,
        use_cache: bool = True,
        search_limit: int = 10,
        template_type: str = 'rag',
        use_web_search: bool = True
    ) -> Dict:
        """Generate content using RAG approach with smart query classification"""
        start_time = time.time()
        
        # Step 1: Classify the query to determine if RAG is needed
        should_use_rag, classification_reason = self.query_classifier.should_use_rag(query)
        
        self.logger.info(f"Query classification: {classification_reason}")
        
        # Step 2: Handle conversational queries without RAG
        if not should_use_rag:
            conversational_response = self.query_classifier.get_conversational_response(query)
            
            return {
                'content': conversational_response,
                'sources': [],
                'query': query,
                'tokens_used': 0,
                'response_time': time.time() - start_time,
                'search_time': 0,
                'web_search_time': 0,
                'kb_search_time': 0,
                'generation_time': 0,
                'cached': False,
                'model_used': 'conversational',
                'finish_reason': 'conversational_response',
                'web_sources_count': 0,
                'kb_sources_count': 0,
                'classification': classification_reason,
                'used_rag': False
            }
        
        # Step 3: Proceed with RAG for factual/research queries
        # Create cache key
        cache_key = self._create_cache_key(query, max_length, temperature, template_type)
        
        # Check cache
        if use_cache:
            cached_result = self.cache_service.get(cache_key)
            if cached_result:
                self.logger.info(f"Cache hit for query: {query[:50]}...")
                self.stats['cache_hits'] += 1
                cached_result['cached'] = True
                cached_result['response_time'] = time.time() - start_time
                return cached_result
        
        # Step 4: Real-time web search for current information
        web_sources = []
        web_search_time = 0
        
        if use_web_search:
            self.logger.info(f"Performing web search for: {query}")
            web_search_start = time.time()
            
            try:
                web_results = self.web_searcher.search_web(query, num_results=5)
                web_search_time = time.time() - web_search_start
                
                # Convert web results to sources format
                for result in web_results:
                    web_sources.append({
                        'title': result['title'],
                        'url': result['url'],
                        'snippet': result['snippet'],
                        'content': result.get('content', result['snippet']),
                        'score': result['score'],
                        'source_type': 'web'
                    })
                
                self.logger.info(f"Found {len(web_sources)} web sources in {web_search_time:.2f}s")
            except Exception as e:
                self.logger.warning(f"Web search failed: {e}")
                web_search_time = time.time() - web_search_start
        
        # Step 5: Semantic search for relevant context from knowledge base
        search_start = time.time()
        search_results = self.vector_service.search(query, search_limit)
        kb_search_time = time.time() - search_start
        
        # Step 6: Combine web sources and knowledge base sources
        all_sources = web_sources.copy()
        
        # Only use knowledge base if web search didn't find enough relevant sources
        if len(web_sources) < 2 and search_results:
            context, kb_sources = self._prepare_context(search_results, query)
            # Filter knowledge base sources by relevance to avoid irrelevant results
            relevant_kb_sources = [
                source for source in kb_sources 
                if source.get('score', 0) >= 0.3  # Higher threshold for KB sources
            ]
            all_sources.extend(relevant_kb_sources)
        
        # Prioritize web sources for freshness
        all_sources.sort(key=lambda x: (x.get('source_type') == 'web', x.get('score', 0)), reverse=True)
        
        # Prepare combined context
        combined_context = self._prepare_combined_context(all_sources, query)
        
        if not combined_context:
            self.logger.warning(f"No relevant context found for query: {query}")
            return self._generate_without_context(query, max_length, temperature)
        
        # Step 7: Generate content with enriched context
        generation_start = time.time()
        generation_result = self.openai_service.generate_with_context(
            query=query,
            context=combined_context,
            template_type=template_type,
            max_tokens=max_length,
            temperature=temperature
        )
        generation_time = time.time() - generation_start
        
        # Step 8: Prepare final result with sources
        result = {
            'content': generation_result.content,
            'sources': all_sources[:5],  # Limit to top 5 sources for display
            'query': query,
            'tokens_used': generation_result.tokens_used,
            'response_time': time.time() - start_time,
            'search_time': kb_search_time + web_search_time,
            'web_search_time': web_search_time,
            'kb_search_time': kb_search_time,
            'generation_time': generation_time,
            'cached': False,
            'model_used': generation_result.model,
            'finish_reason': generation_result.finish_reason,
            'web_sources_count': len(web_sources),
            'kb_sources_count': len(all_sources) - len(web_sources),
            'classification': classification_reason,
            'used_rag': True
        }
        
        # Debug log for sources
        self.logger.info(f"Final sources for query '{query}': {len(all_sources)} total")
        for i, source in enumerate(all_sources[:5]):
            self.logger.info(f"Source {i+1}: {source.get('source_type', 'unknown')} - {source.get('title', 'no title')[:50]}")
        
        # Cache the result
        if use_cache:
            self.cache_service.set(cache_key, result, ttl=3600)  # Cache for 1 hour
        
        # Update statistics
        self._update_stats(time.time() - start_time, kb_search_time + web_search_time, generation_time)
        
        return result
    
    def _prepare_context(self, search_results: List[SearchResult], query: str) -> Tuple[str, List[Dict]]:
        """Prepare context from search results"""
        if not search_results:
            return "", []
        
        # Filter results by relevance threshold
        relevant_results = [
            result for result in search_results 
            if result.score >= self.relevance_threshold
        ]
        
        if not relevant_results:
            # Use top results even if below threshold
            relevant_results = search_results[:self.min_search_results]
        
        # Prepare context text and source information
        context_parts = []
        sources = []
        current_length = 0
        
        for i, result in enumerate(relevant_results):
            # Estimate token count (rough approximation)
            content_tokens = len(result.content.split()) * 1.3  # Account for subword tokens
            
            if current_length + content_tokens > self.max_context_length:
                break
            
            # Add to context
            context_part = f"Source {i+1}: {result.content}"
            context_parts.append(context_part)
            current_length += content_tokens
            
            # Add source information
            sources.append({
                'id': result.id,
                'title': result.title,
                'url': result.url,
                'score': result.score,
                'snippet': result.content[:200] + "..." if len(result.content) > 200 else result.content,
                'source_type': 'knowledge_base'
            })
        
        context = "\n\n".join(context_parts)
        return context, sources
    
    def _prepare_combined_context(self, sources: List[Dict], query: str) -> str:
        """Prepare combined context from web and knowledge base sources"""
        if not sources:
            return ""
        
        context_parts = []
        current_length = 0
        
        for i, source in enumerate(sources):
            content = source.get('content', source.get('snippet', ''))
            if not content:
                continue
                
            # Estimate token count
            content_tokens = len(content.split()) * 1.3
            
            if current_length + content_tokens > self.max_context_length:
                break
            
            # Add source type prefix for clarity
            source_type = source.get('source_type', 'unknown')
            context_part = f"[{source_type.upper()} SOURCE {i+1}]: {content}"
            context_parts.append(context_part)
            current_length += content_tokens
        
        return "\n\n".join(context_parts)
    
    def _generate_without_context(self, query: str, max_length: int, temperature: float) -> Dict:
        """Generate content without RAG context when no relevant sources found"""
        generation_start = time.time()
        
        generation_result = self.openai_service.generate_content(
            prompt=f"Please provide a helpful response to: {query}",
            max_tokens=max_length,
            temperature=temperature
        )
        
        generation_time = time.time() - generation_start
        
        return {
            'content': generation_result.content,
            'sources': [],
            'query': query,
            'tokens_used': generation_result.tokens_used,
            'response_time': generation_time,
            'search_time': 0,
            'web_search_time': 0,
            'kb_search_time': 0,
            'generation_time': generation_time,
            'cached': False,
            'model_used': generation_result.model,
            'finish_reason': generation_result.finish_reason,
            'web_sources_count': 0,
            'kb_sources_count': 0,
            'classification': 'no_context_available',
            'used_rag': False
        }
    
    def generate_summary(self, content: str, max_length: int = 200) -> Dict:
        """Generate a summary of the given content"""
        start_time = time.time()
        
        # Search for related context
        search_results = self.vector_service.search(content, limit=5)
        
        if search_results:
            context, sources = self._prepare_context(search_results, content)
        else:
            context, sources = "", []
        
        # Generate summary
        generation_result = self.openai_service.generate_with_context(
            query=f"Summarize this content in {max_length} words or less",
            context=f"Content to summarize:\n{content}\n\nRelated context:\n{context}",
            template_type='summary',
            max_tokens=max_length,
            temperature=0.3
        )
        
        return {
            'content': generation_result.content,
            'sources': sources,
            'query': 'summary_request',
            'tokens_used': generation_result.tokens_used,
            'response_time': time.time() - start_time,
            'model_used': generation_result.model
        }
    
    def generate_qa(self, question: str, max_length: int = 300) -> Dict:
        """Generate Q&A style response"""
        start_time = time.time()
        
        # Use semantic search for context
        search_results = self.vector_service.search(question, limit=8)
        
        if not search_results:
            return self._generate_without_context(question, max_length, 0.7)
        
        context, sources = self._prepare_context(search_results, question)
        prompt = f"Question: {question}\n\nAnswer based on the following context:"
        
        generation_result = self.openai_service.generate_with_context(
            query=prompt,
            context=context,
            template_type='qa',
            max_tokens=max_length,
            temperature=0.5
        )
        
        return {
            'content': generation_result.content,
            'sources': sources,
            'query': question,
            'tokens_used': generation_result.tokens_used,
            'response_time': time.time() - start_time,
            'model_used': generation_result.model
        }
    
    def _create_cache_key(self, query: str, max_length: int, temperature: float, template_type: str) -> str:
        """Create a cache key for the request"""
        key_data = f"{query}:{max_length}:{temperature}:{template_type}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _update_stats(self, response_time: float, search_time: float, generation_time: float):
        """Update service statistics"""
        self.stats['total_requests'] += 1
        
        # Update running averages
        total = self.stats['total_requests']
        self.stats['average_response_time'] = (
            (self.stats['average_response_time'] * (total - 1) + response_time) / total
        )
        self.stats['average_search_time'] = (
            (self.stats['average_search_time'] * (total - 1) + search_time) / total
        )
        self.stats['average_generation_time'] = (
            (self.stats['average_generation_time'] * (total - 1) + generation_time) / total
        )
    
    def get_stats(self) -> Dict:
        """Get service statistics"""
        return self.stats.copy()
    
    def clear_cache(self):
        """Clear the cache"""
        self.cache_service.clear()
        self.logger.info("Cache cleared")
    
    def health_check(self) -> Dict:
        """Perform health check"""
        try:
            # Test vector service
            test_results = self.vector_service.search("test", limit=1)
            vector_status = "healthy"
        except Exception as e:
            vector_status = f"error: {str(e)}"
        
        try:
            # Test cache service
            self.cache_service.set("health_check", "test", ttl=1)
            cache_status = "healthy"
        except Exception as e:
            cache_status = f"error: {str(e)}"
        
        return {
            'status': 'healthy' if vector_status == 'healthy' and cache_status == 'healthy' else 'degraded',
            'vector_service': vector_status,
            'cache_service': cache_status,
            'stats': self.get_stats()
        }