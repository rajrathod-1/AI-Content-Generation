"""
Intelligent web crawler for data ingestion
Processes large amounts of text data for the knowledge base
"""
import requests
from bs4 import BeautifulSoup
import time
import logging
import os
import json
import hashlib
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Set
import re
from dataclasses import dataclass
import asyncio
import aiohttp
from asyncio_throttle import Throttler
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
import pandas as pd

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

@dataclass
class Document:
    """Document data structure"""
    url: str
    title: str
    content: str
    metadata: Dict
    hash: str
    timestamp: float

class TextProcessor:
    """Advanced text processing and cleaning"""
    
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.logger = logging.getLogger(__name__)
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\!\?\,\;\:\-\(\)]', '', text)
        
        # Remove very short lines (likely navigation/menu items)
        lines = text.split('\n')
        cleaned_lines = [line.strip() for line in lines if len(line.strip()) > 20]
        
        return '\n'.join(cleaned_lines)
    
    def extract_sentences(self, text: str, min_length: int = 50) -> List[str]:
        """Extract meaningful sentences from text"""
        sentences = sent_tokenize(text)
        
        # Filter sentences by length and content quality
        quality_sentences = []
        for sentence in sentences:
            if (len(sentence) >= min_length and 
                len(word_tokenize(sentence)) >= 5 and
                not self._is_low_quality_sentence(sentence)):
                quality_sentences.append(sentence.strip())
        
        return quality_sentences
    
    def _is_low_quality_sentence(self, sentence: str) -> bool:
        """Check if sentence is low quality (navigation, ads, etc.)"""
        low_quality_patterns = [
            r'^(click|subscribe|follow|share|like)',
            r'(cookies?|privacy policy|terms of service)',
            r'^(home|about|contact|login|register)',
            r'(advertisement|sponsored|ad)',
            r'^[\d\s\-\.\,]+$',  # Only numbers and punctuation
        ]
        
        sentence_lower = sentence.lower()
        return any(re.search(pattern, sentence_lower) for pattern in low_quality_patterns)
    
    def extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract metadata from HTML"""
        metadata = {
            'url': url,
            'domain': urlparse(url).netloc,
            'title': '',
            'description': '',
            'keywords': [],
            'author': '',
            'published_date': '',
            'language': 'en'
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text().strip()
        
        # Extract meta tags
        meta_tags = soup.find_all('meta')
        for tag in meta_tags:
            if tag.get('name') == 'description':
                metadata['description'] = tag.get('content', '')
            elif tag.get('name') == 'keywords':
                keywords = tag.get('content', '')
                metadata['keywords'] = [k.strip() for k in keywords.split(',')]
            elif tag.get('name') == 'author':
                metadata['author'] = tag.get('content', '')
            elif tag.get('property') == 'article:published_time':
                metadata['published_date'] = tag.get('content', '')
        
        return metadata

class WebCrawler:
    """Intelligent web crawler with rate limiting and content extraction"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.delay = config.get('CRAWL_DELAY', 1.0)
        self.max_pages = config.get('MAX_CRAWL_PAGES', 1000)
        self.data_dir = config.get('DATA_DIRECTORY', './data/raw')
        self.processed_dir = config.get('PROCESSED_DATA_DIRECTORY', './data/processed')
        self.batch_size = config.get('BATCH_SIZE', 100)
        
        self.visited_urls: Set[str] = set()
        self.documents: List[Document] = []
        self.text_processor = TextProcessor()
        self.logger = logging.getLogger(__name__)
        
        # Create directories
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.processed_dir, exist_ok=True)
        
        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; ContentBot/1.0; Research Purpose)'
        })
    
    def crawl_urls(self, urls: List[str]) -> List[Document]:
        """Crawl a list of URLs and extract content"""
        self.logger.info(f"Starting crawl of {len(urls)} URLs")
        
        for i, url in enumerate(urls):
            if i >= self.max_pages:
                break
                
            if url in self.visited_urls:
                continue
            
            try:
                document = self._crawl_single_url(url)
                if document:
                    self.documents.append(document)
                    self.visited_urls.add(url)
                    
                    # Save in batches
                    if len(self.documents) % self.batch_size == 0:
                        self._save_batch()
                
                # Rate limiting
                time.sleep(self.delay)
                
            except Exception as e:
                self.logger.error(f"Error crawling {url}: {str(e)}")
                continue
        
        # Save remaining documents
        if self.documents:
            self._save_batch()
        
        self.logger.info(f"Crawl completed. Processed {len(self.visited_urls)} URLs")
        return self.documents
    
    def _crawl_single_url(self, url: str) -> Document:
        """Crawl a single URL and extract content"""
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
                element.decompose()
            
            # Extract main content
            content = self._extract_main_content(soup)
            if not content or len(content) < 100:
                return None
            
            # Clean and process text
            cleaned_content = self.text_processor.clean_text(content)
            
            # Extract metadata
            metadata = self.text_processor.extract_metadata(soup, url)
            
            # Create document hash for deduplication
            content_hash = hashlib.md5(cleaned_content.encode()).hexdigest()
            
            return Document(
                url=url,
                title=metadata['title'],
                content=cleaned_content,
                metadata=metadata,
                hash=content_hash,
                timestamp=time.time()
            )
            
        except Exception as e:
            self.logger.error(f"Error processing {url}: {str(e)}")
            return None
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML using heuristics"""
        # Try to find main content areas
        content_selectors = [
            'main',
            'article',
            '.content',
            '.main-content',
            '.post-content',
            '.entry-content',
            '[role="main"]'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                return ' '.join([elem.get_text(strip=True) for elem in elements])
        
        # Fallback: extract from body, excluding navigation
        body = soup.find('body')
        if body:
            # Remove navigation elements
            for nav in body.find_all(['nav', 'header', 'footer', 'aside']):
                nav.decompose()
            return body.get_text(strip=True)
        
        return soup.get_text(strip=True)
    
    def _save_batch(self):
        """Save current batch of documents"""
        if not self.documents:
            return
        
        timestamp = int(time.time())
        filename = f"crawled_batch_{timestamp}.json"
        filepath = os.path.join(self.data_dir, filename)
        
        # Convert documents to dict for JSON serialization
        doc_dicts = []
        for doc in self.documents:
            doc_dicts.append({
                'url': doc.url,
                'title': doc.title,
                'content': doc.content,
                'metadata': doc.metadata,
                'hash': doc.hash,
                'timestamp': doc.timestamp
            })
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(doc_dicts, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved batch of {len(self.documents)} documents to {filename}")
        self.documents.clear()

class DataProcessor:
    """Process and prepare crawled data for vector database"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.data_dir = config.get('DATA_DIRECTORY', './data/raw')
        self.processed_dir = config.get('PROCESSED_DATA_DIRECTORY', './data/processed')
        self.text_processor = TextProcessor()
        self.logger = logging.getLogger(__name__)
    
    def process_all_files(self) -> List[Dict]:
        """Process all crawled data files"""
        processed_documents = []
        
        # Get all JSON files from data directory
        json_files = [f for f in os.listdir(self.data_dir) if f.endswith('.json')]
        
        for filename in json_files:
            filepath = os.path.join(self.data_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    documents = json.load(f)
                
                for doc in documents:
                    processed_doc = self._process_document(doc)
                    if processed_doc:
                        processed_documents.append(processed_doc)
                
            except Exception as e:
                self.logger.error(f"Error processing file {filename}: {str(e)}")
        
        # Remove duplicates based on content hash
        processed_documents = self._deduplicate_documents(processed_documents)
        
        # Save processed documents
        self._save_processed_documents(processed_documents)
        
        self.logger.info(f"Processed {len(processed_documents)} unique documents")
        return processed_documents
    
    def _process_document(self, doc: Dict) -> Dict:
        """Process a single document"""
        try:
            content = doc.get('content', '')
            if len(content) < 100:  # Skip very short documents
                return None
            
            # Extract sentences for better chunk management
            sentences = self.text_processor.extract_sentences(content)
            if len(sentences) < 3:
                return None
            
            # Create chunks for better retrieval
            chunks = self._create_chunks(sentences)
            
            return {
                'id': doc.get('hash', ''),
                'url': doc.get('url', ''),
                'title': doc.get('title', ''),
                'content': content,
                'chunks': chunks,
                'metadata': doc.get('metadata', {}),
                'processed_timestamp': time.time()
            }
            
        except Exception as e:
            self.logger.error(f"Error processing document: {str(e)}")
            return None
    
    def _create_chunks(self, sentences: List[str], chunk_size: int = 5) -> List[Dict]:
        """Create overlapping chunks from sentences"""
        chunks = []
        
        for i in range(0, len(sentences), chunk_size - 1):  # Overlap by 1 sentence
            chunk_sentences = sentences[i:i + chunk_size]
            chunk_text = ' '.join(chunk_sentences)
            
            if len(chunk_text) > 50:  # Minimum chunk length
                chunks.append({
                    'text': chunk_text,
                    'start_sentence': i,
                    'sentence_count': len(chunk_sentences)
                })
        
        return chunks
    
    def _deduplicate_documents(self, documents: List[Dict]) -> List[Dict]:
        """Remove duplicate documents based on content hash"""
        seen_hashes = set()
        unique_documents = []
        
        for doc in documents:
            doc_hash = doc.get('id')
            if doc_hash and doc_hash not in seen_hashes:
                seen_hashes.add(doc_hash)
                unique_documents.append(doc)
        
        return unique_documents
    
    def _save_processed_documents(self, documents: List[Dict]):
        """Save processed documents"""
        timestamp = int(time.time())
        filename = f"processed_documents_{timestamp}.json"
        filepath = os.path.join(self.processed_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(documents, f, indent=2, ensure_ascii=False)
        
        # Also save as CSV for easy analysis
        csv_filename = f"processed_documents_{timestamp}.csv"
        csv_filepath = os.path.join(self.processed_dir, csv_filename)
        
        # Flatten data for CSV
        csv_data = []
        for doc in documents:
            csv_data.append({
                'id': doc['id'],
                'url': doc['url'],
                'title': doc['title'],
                'content_length': len(doc['content']),
                'chunk_count': len(doc['chunks']),
                'domain': doc['metadata'].get('domain', ''),
                'processed_timestamp': doc['processed_timestamp']
            })
        
        df = pd.DataFrame(csv_data)
        df.to_csv(csv_filepath, index=False)
        
        self.logger.info(f"Saved processed documents to {filename} and {csv_filename}")

# Example usage and sample data sources
SAMPLE_URLS = [
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    "https://en.wikipedia.org/wiki/Machine_learning",
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://en.wikipedia.org/wiki/Deep_learning",
    "https://en.wikipedia.org/wiki/Computer_vision",
    "https://en.wikipedia.org/wiki/Data_science",
    "https://en.wikipedia.org/wiki/Big_data",
    "https://en.wikipedia.org/wiki/Cloud_computing",
    "https://en.wikipedia.org/wiki/Internet_of_things",
    "https://en.wikipedia.org/wiki/Blockchain"
]

if __name__ == "__main__":
    # Example usage
    config = {
        'CRAWL_DELAY': 2.0,
        'MAX_CRAWL_PAGES': 50,
        'DATA_DIRECTORY': './data/raw',
        'PROCESSED_DATA_DIRECTORY': './data/processed',
        'BATCH_SIZE': 10
    }
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Crawl sample URLs
    crawler = WebCrawler(config)
    crawler.crawl_urls(SAMPLE_URLS)
    
    # Process crawled data
    processor = DataProcessor(config)
    processed_docs = processor.process_all_files()
    
    print(f"Successfully processed {len(processed_docs)} documents")