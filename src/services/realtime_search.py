"""
Real-time web search service for RAG
Performs live web searches and extracts relevant content
"""
import requests
from bs4 import BeautifulSoup
import logging
import time
from typing import Dict, List, Optional
from urllib.parse import quote
import json
import re

class RealTimeWebSearcher:
    """Service for real-time web searching and content extraction"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def search_web(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Perform real-time web search and extract content
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results with content and sources
        """
        try:
            self.logger.info(f"Performing web search for: {query}")
            
            # Use DuckDuckGo for search (no API key required)
            search_results = self._search_duckduckgo(query, num_results)
            
            # Extract content from each result
            enriched_results = []
            for result in search_results:
                try:
                    content = self._extract_content(result['url'])
                    if content:
                        enriched_results.append({
                            'title': result['title'],
                            'url': result['url'],
                            'snippet': result['snippet'],
                            'content': content,
                            'score': result.get('score', 0.8),
                            'timestamp': time.time()
                        })
                        
                        # Limit to prevent timeout
                        if len(enriched_results) >= num_results:
                            break
                            
                except Exception as e:
                    self.logger.warning(f"Failed to extract content from {result.get('url', 'unknown')}: {str(e)}")
                    continue
                    
            self.logger.info(f"Successfully extracted content from {len(enriched_results)} sources")
            return enriched_results
            
        except Exception as e:
            self.logger.error(f"Web search failed: {str(e)}")
            return []
    
    def _search_duckduckgo(self, query: str, num_results: int) -> List[Dict]:
        """Search using DuckDuckGo"""
        try:
            # DuckDuckGo instant answer API
            search_url = f"https://api.duckduckgo.com/"
            params = {
                'q': query,
                'format': 'json',
                'no_html': '1',
                'skip_disambig': '1'
            }
            
            response = self.session.get(search_url, params=params, timeout=10)
            data = response.json()
            
            results = []
            
            # Get abstract if available
            if data.get('Abstract'):
                results.append({
                    'title': data.get('AbstractText', 'DuckDuckGo Abstract'),
                    'url': data.get('AbstractURL', ''),
                    'snippet': data.get('Abstract', '')[:200],
                    'score': 0.9
                })
            
            # Get related topics
            for topic in data.get('RelatedTopics', [])[:num_results-1]:
                if isinstance(topic, dict) and topic.get('Text'):
                    results.append({
                        'title': topic.get('Text', '').split(' - ')[0],
                        'url': topic.get('FirstURL', ''),
                        'snippet': topic.get('Text', '')[:200],
                        'score': 0.7
                    })
            
            # If we don't have enough results, try web scraping approach
            if len(results) < 2:
                results.extend(self._scrape_search_results(query, num_results))
            
            return results[:num_results]
            
        except Exception as e:
            self.logger.error(f"DuckDuckGo search failed: {str(e)}")
            return self._scrape_search_results(query, num_results)
    
    def _scrape_search_results(self, query: str, num_results: int) -> List[Dict]:
        """Fallback: scrape search results from multiple sources"""
        results = []
        
        # Try multiple search sources
        sources = [
            self._search_bing,
            self._search_wikipedia,
        ]
        
        for search_func in sources:
            try:
                source_results = search_func(query, num_results - len(results))
                results.extend(source_results)
                
                if len(results) >= num_results:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Search source failed: {str(e)}")
                continue
        
        return results[:num_results]
    
    def _search_bing(self, query: str, num_results: int) -> List[Dict]:
        """Search using Bing (web scraping)"""
        try:
            search_url = f"https://www.bing.com/search"
            params = {'q': query}
            
            response = self.session.get(search_url, params=params, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = []
            
            # Find search results
            for result in soup.find_all('li', class_='b_algo')[:num_results]:
                title_elem = result.find('h2')
                desc_elem = result.find('p')
                
                if title_elem and desc_elem:
                    link_elem = title_elem.find('a')
                    if link_elem:
                        results.append({
                            'title': title_elem.get_text().strip(),
                            'url': link_elem.get('href', ''),
                            'snippet': desc_elem.get_text().strip()[:200],
                            'score': 0.6
                        })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Bing search failed: {str(e)}")
            return []
    
    def _search_wikipedia(self, query: str, num_results: int) -> List[Dict]:
        """Search Wikipedia for relevant articles"""
        try:
            # Wikipedia API search
            search_url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(query)
            
            response = self.session.get(search_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('extract'):
                    return [{
                        'title': data.get('title', 'Wikipedia Article'),
                        'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                        'snippet': data.get('extract', '')[:200],
                        'score': 0.8
                    }]
            
            return []
            
        except Exception as e:
            self.logger.error(f"Wikipedia search failed: {str(e)}")
            return []
    
    def _extract_content(self, url: str) -> Optional[str]:
        """Extract main content from a webpage"""
        try:
            if not url or not url.startswith(('http://', 'https://')):
                return None
                
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Try to find main content
            content_selectors = [
                'article',
                '[role="main"]',
                '.content',
                '.main-content',
                '#content',
                'main',
                '.post-content',
                '.entry-content'
            ]
            
            content_text = ""
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content_text = elements[0].get_text()
                    break
            
            # Fallback to body if no specific content found
            if not content_text:
                body = soup.find('body')
                if body:
                    content_text = body.get_text()
            
            # Clean up the text
            lines = (line.strip() for line in content_text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content_text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit content length
            if len(content_text) > 2000:
                content_text = content_text[:2000] + "..."
            
            return content_text if len(content_text) > 100 else None
            
        except Exception as e:
            self.logger.warning(f"Content extraction failed for {url}: {str(e)}")
            return None