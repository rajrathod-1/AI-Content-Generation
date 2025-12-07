"""
Vector database service using FAISS and Sentence-Transformers
Handles embedding generation and semantic search
"""
import os
import json
import pickle
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
import faiss
from sentence_transformers import SentenceTransformer
import hashlib
import time
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Search result data structure"""
    id: str
    content: str
    title: str
    score: float
    metadata: Dict
    url: str

class VectorService:
    """FAISS-based vector database service"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.model_name = config.get('EMBEDDINGS_MODEL', 'all-MiniLM-L6-v2')
        self.vector_dim = config.get('VECTOR_DIMENSION', 384)
        self.index_path = config.get('FAISS_INDEX_PATH', './data/faiss_index')
        self.max_results = config.get('MAX_SEARCH_RESULTS', 10)
        
        self.logger = logging.getLogger(__name__)
        
        # Initialize sentence transformer
        self.logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        
        # Verify vector dimension matches model
        test_embedding = self.model.encode(["test"])
        actual_dim = test_embedding.shape[1]
        if actual_dim != self.vector_dim:
            self.logger.warning(f"Vector dimension mismatch. Expected: {self.vector_dim}, Actual: {actual_dim}")
            self.vector_dim = actual_dim
        
        # Initialize FAISS index
        self.index = None
        self.documents = []
        self.id_to_doc = {}
        
        # Create directories
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        
        # Load existing index if available
        self._load_index()
    
    def _load_index(self):
        """Load existing FAISS index and documents"""
        index_file = f"{self.index_path}.index"
        docs_file = f"{self.index_path}_docs.json"
        mapping_file = f"{self.index_path}_mapping.pkl"
        
        if os.path.exists(index_file) and os.path.exists(docs_file):
            try:
                # Load FAISS index
                self.index = faiss.read_index(index_file)
                
                # Load documents
                with open(docs_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
                
                # Load ID mapping
                if os.path.exists(mapping_file):
                    with open(mapping_file, 'rb') as f:
                        self.id_to_doc = pickle.load(f)
                
                self.logger.info(f"Loaded existing index with {len(self.documents)} documents")
                
            except Exception as e:
                self.logger.error(f"Error loading index: {str(e)}")
                self._initialize_new_index()
        else:
            self._initialize_new_index()
    
    def _initialize_new_index(self):
        """Initialize a new FAISS index"""
        self.index = faiss.IndexFlatIP(self.vector_dim)  # Inner product for cosine similarity
        self.documents = []
        self.id_to_doc = {}
        self.logger.info("Initialized new FAISS index")
    
    def _save_index(self):
        """Save FAISS index and documents to disk"""
        try:
            index_file = f"{self.index_path}.index"
            docs_file = f"{self.index_path}_docs.json"
            mapping_file = f"{self.index_path}_mapping.pkl"
            
            # Save FAISS index
            faiss.write_index(self.index, index_file)
            
            # Save documents
            with open(docs_file, 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
            
            # Save ID mapping
            with open(mapping_file, 'wb') as f:
                pickle.dump(self.id_to_doc, f)
            
            self.logger.info(f"Saved index with {len(self.documents)} documents")
            
        except Exception as e:
            self.logger.error(f"Error saving index: {str(e)}")
    
    def add_documents(self, documents: List[Dict]) -> int:
        """Add documents to the vector database"""
        if not documents:
            return 0
        
        processed_count = 0
        texts_to_embed = []
        docs_to_add = []
        
        for doc in documents:
            try:
                # Validate document structure
                if not all(key in doc for key in ['content', 'title', 'url']):
                    continue
                
                # Generate document ID if not provided
                doc_id = doc.get('id')
                if not doc_id:
                    content_hash = hashlib.md5(doc['content'].encode()).hexdigest()
                    doc_id = f"doc_{content_hash}"
                
                # Skip if document already exists
                if doc_id in self.id_to_doc:
                    continue
                
                # Process chunks if available, otherwise use full content
                if 'chunks' in doc and doc['chunks']:
                    for i, chunk in enumerate(doc['chunks']):
                        chunk_id = f"{doc_id}_chunk_{i}"
                        chunk_doc = {
                            'id': chunk_id,
                            'content': chunk['text'],
                            'title': doc['title'],
                            'url': doc['url'],
                            'metadata': {
                                **doc.get('metadata', {}),
                                'parent_doc_id': doc_id,
                                'chunk_index': i,
                                'is_chunk': True
                            }
                        }
                        
                        texts_to_embed.append(chunk['text'])
                        docs_to_add.append(chunk_doc)
                        self.id_to_doc[chunk_id] = len(self.documents) + len(docs_to_add) - 1
                else:
                    # Use full document content
                    doc_with_id = {
                        'id': doc_id,
                        'content': doc['content'],
                        'title': doc['title'],
                        'url': doc['url'],
                        'metadata': {
                            **doc.get('metadata', {}),
                            'is_chunk': False
                        }
                    }
                    
                    texts_to_embed.append(doc['content'])
                    docs_to_add.append(doc_with_id)
                    self.id_to_doc[doc_id] = len(self.documents) + len(docs_to_add) - 1
                
            except Exception as e:
                self.logger.error(f"Error processing document: {str(e)}")
                continue
        
        if not texts_to_embed:
            return 0
        
        try:
            # Generate embeddings
            self.logger.info(f"Generating embeddings for {len(texts_to_embed)} texts")
            embeddings = self.model.encode(texts_to_embed, convert_to_tensor=False, show_progress_bar=True)
            
            # Normalize embeddings for cosine similarity
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Add to FAISS index
            embeddings_array = np.array(embeddings).astype('float32')
            self.index.add(embeddings_array)
            
            # Add documents to collection
            self.documents.extend(docs_to_add)
            processed_count = len(docs_to_add)
            
            # Save index
            self._save_index()
            
            self.logger.info(f"Added {processed_count} documents to vector database")
            
        except Exception as e:
            self.logger.error(f"Error adding documents to index: {str(e)}")
            return 0
        
        return processed_count
    
    def search(self, query: str, limit: Optional[int] = None) -> List[SearchResult]:
        """Perform semantic search"""
        if not query.strip():
            return []
        
        if limit is None:
            limit = self.max_results
        
        if not self.index or self.index.ntotal == 0:
            self.logger.warning("No documents in index")
            return []
        
        try:
            # Generate query embedding
            query_embedding = self.model.encode([query], convert_to_tensor=False)
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
            query_vector = query_embedding.astype('float32')
            
            # Search in FAISS index
            search_limit = min(limit, self.index.ntotal)
            scores, indices = self.index.search(query_vector, search_limit)
            
            # Convert results
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.documents):  # Valid index
                    doc = self.documents[idx]
                    result = SearchResult(
                        id=doc['id'],
                        content=doc['content'][:500] + "..." if len(doc['content']) > 500 else doc['content'],
                        title=doc['title'],
                        score=float(score),
                        metadata=doc['metadata'],
                        url=doc['url']
                    )
                    results.append(result)
            
            # Sort by score (descending)
            results.sort(key=lambda x: x.score, reverse=True)
            
            self.logger.info(f"Search for '{query}' returned {len(results)} results")
            return results
            
        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            return []
    
    def search_by_filters(self, query: str, filters: Dict, limit: Optional[int] = None) -> List[SearchResult]:
        """Search with metadata filters"""
        # Get all results first
        all_results = self.search(query, self.index.ntotal if self.index else 0)
        
        # Apply filters
        filtered_results = []
        for result in all_results:
            metadata = result.metadata
            match = True
            
            for key, value in filters.items():
                if key not in metadata or metadata[key] != value:
                    match = False
                    break
            
            if match:
                filtered_results.append(result)
                if limit and len(filtered_results) >= limit:
                    break
        
        return filtered_results
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a document by ID"""
        if doc_id in self.id_to_doc:
            doc_index = self.id_to_doc[doc_id]
            if 0 <= doc_index < len(self.documents):
                return self.documents[doc_index]
        return None
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        return {
            'total_documents': len(self.documents),
            'vector_dimension': self.vector_dim,
            'model_name': self.model_name,
            'index_size': self.index.ntotal if self.index else 0,
            'last_updated': time.time()
        }
    
    def rebuild_index(self) -> bool:
        """Rebuild the entire index from documents"""
        try:
            if not self.documents:
                self.logger.warning("No documents to rebuild index")
                return False
            
            # Extract all content
            texts = [doc['content'] for doc in self.documents]
            
            # Generate embeddings
            self.logger.info(f"Rebuilding index with {len(texts)} documents")
            embeddings = self.model.encode(texts, convert_to_tensor=False, show_progress_bar=True)
            
            # Normalize embeddings
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
            
            # Create new index
            new_index = faiss.IndexFlatIP(self.vector_dim)
            embeddings_array = np.array(embeddings).astype('float32')
            new_index.add(embeddings_array)
            
            # Replace old index
            self.index = new_index
            
            # Rebuild ID mapping
            self.id_to_doc = {}
            for i, doc in enumerate(self.documents):
                self.id_to_doc[doc['id']] = i
            
            # Save new index
            self._save_index()
            
            self.logger.info("Index rebuilt successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error rebuilding index: {str(e)}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index (requires rebuild)"""
        if doc_id not in self.id_to_doc:
            return False
        
        try:
            # Remove from documents list
            doc_index = self.id_to_doc[doc_id]
            del self.documents[doc_index]
            
            # Remove from ID mapping
            del self.id_to_doc[doc_id]
            
            # Update remaining mappings
            for doc_id_key, index in self.id_to_doc.items():
                if index > doc_index:
                    self.id_to_doc[doc_id_key] = index - 1
            
            # Rebuild index
            return self.rebuild_index()
            
        except Exception as e:
            self.logger.error(f"Error deleting document {doc_id}: {str(e)}")
            return False
    
    def clear_index(self):
        """Clear all documents and rebuild empty index"""
        self.documents = []
        self.id_to_doc = {}
        self._initialize_new_index()
        self._save_index()
        self.logger.info("Index cleared")

# Example usage and testing
if __name__ == "__main__":
    # Example configuration
    config = {
        'EMBEDDINGS_MODEL': 'all-MiniLM-L6-v2',
        'VECTOR_DIMENSION': 384,
        'FAISS_INDEX_PATH': './data/faiss_index',
        'MAX_SEARCH_RESULTS': 10
    }
    
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize vector service
    vector_service = VectorService(config)
    
    # Sample documents
    sample_docs = [
        {
            'id': 'doc1',
            'title': 'Introduction to Machine Learning',
            'content': 'Machine learning is a subset of artificial intelligence that focuses on algorithms that can learn from data.',
            'url': 'https://example.com/ml-intro',
            'metadata': {'category': 'AI', 'difficulty': 'beginner'}
        },
        {
            'id': 'doc2',
            'title': 'Deep Learning Fundamentals',
            'content': 'Deep learning uses neural networks with multiple layers to model and understand complex patterns in data.',
            'url': 'https://example.com/dl-fundamentals',
            'metadata': {'category': 'AI', 'difficulty': 'intermediate'}
        }
    ]
    
    # Add documents
    vector_service.add_documents(sample_docs)
    
    # Perform search
    results = vector_service.search("What is machine learning?")
    for result in results:
        print(f"Title: {result.title}")
        print(f"Score: {result.score:.4f}")
        print(f"Content: {result.content}")
        print("---")
    
    # Get stats
    stats = vector_service.get_stats()
    print(f"Database stats: {stats}")