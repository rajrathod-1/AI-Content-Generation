"""
Vector database service using FAISS and OpenAI embeddings
Handles embedding generation and semantic search
"""
import os
import json
import logging
import hashlib
import time
from dataclasses import dataclass
from typing import List, Dict, Optional

import numpy as np
import faiss
from openai import OpenAI

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
    """FAISS index over OpenAI embeddings. No local model, so it fits small and serverless hosts."""

    def __init__(self, config: Dict, client: Optional[OpenAI] = None):
        self.model_name = config.get('EMBEDDINGS_MODEL', 'text-embedding-3-small')
        self.vector_dim = config.get('VECTOR_DIMENSION', 384)
        self.index_path = config.get('FAISS_INDEX_PATH', './data/faiss_index')
        self.max_results = config.get('MAX_SEARCH_RESULTS', 10)
        self.logger = logging.getLogger(__name__)
        self.client = client or OpenAI(api_key=config.get('OPENAI_API_KEY'), timeout=30.0, max_retries=2)

        self.documents: List[Dict] = []
        self.id_to_doc: Dict[str, int] = {}
        self.index = faiss.IndexFlatIP(self.vector_dim)  # inner product on unit vectors = cosine
        self._load_index()

    def _embed(self, texts: List[str]) -> np.ndarray:
        """Unit-length float32 vectors, one row per text."""
        vectors = []
        for start in range(0, len(texts), 256):
            response = self.client.embeddings.create(
                model=self.model_name, input=texts[start:start + 256], dimensions=self.vector_dim)
            vectors.extend(item.embedding for item in response.data)
        arr = np.array(vectors, dtype='float32')
        return arr / np.linalg.norm(arr, axis=1, keepdims=True)

    def _reindex(self):
        """Embed every stored document into a fresh index."""
        index = faiss.IndexFlatIP(self.vector_dim)
        if self.documents:
            index.add(self._embed([doc['content'] for doc in self.documents]))
        self.index = index
        self.id_to_doc = {doc['id']: i for i, doc in enumerate(self.documents)}

    def _ensure_index(self):
        """Self-heal if embedding failed at startup (e.g. a network blip on a cold start)."""
        if self.index.ntotal != len(self.documents):
            self._reindex()

    def _load_index(self):
        """Load stored documents and embed them.

        Only documents are persisted, never vectors, so changing the embedding model can't
        leave a stale index behind.
        """
        # ponytail: re-embeds the whole knowledge base on every start (one API call for today's
        # handful of docs); persist vectors tagged with the model name if the KB grows large
        docs_file = f"{self.index_path}_docs.json"
        if not os.path.exists(docs_file):
            self.logger.info("No stored documents; starting with an empty index")
            return
        with open(docs_file, 'r', encoding='utf-8') as f:
            self.documents = json.load(f)
        try:
            self._reindex()
            self.logger.info(f"Embedded {len(self.documents)} documents with {self.model_name}")
        except Exception as e:
            # Documents stay loaded; search retries the embedding via _ensure_index
            self.logger.error(f"Embedding stored documents failed: {e}")

    def _save_index(self):
        """Persist documents (read-only hosts such as serverless functions keep them in memory only)."""
        try:
            os.makedirs(os.path.dirname(self.index_path) or '.', exist_ok=True)
            with open(f"{self.index_path}_docs.json", 'w', encoding='utf-8') as f:
                json.dump(self.documents, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved {len(self.documents)} documents")
        except OSError as e:
            self.logger.error(f"Documents not persisted (read-only filesystem?): {e}")

    def add_documents(self, documents: List[Dict]) -> int:
        """Add documents (or their chunks) to the index. Returns how many entries were added."""
        new_docs = []
        for doc in documents:
            if not isinstance(doc, dict) or not all(key in doc for key in ('content', 'title', 'url')):
                continue
            doc_id = doc.get('id') or f"doc_{hashlib.md5(doc['content'].encode()).hexdigest()}"
            if doc_id in self.id_to_doc:
                continue
            metadata = doc.get('metadata', {})
            chunks = doc.get('chunks') or []
            if chunks:
                new_docs += [{
                    'id': f"{doc_id}_chunk_{i}",
                    'content': chunk['text'],
                    'title': doc['title'],
                    'url': doc['url'],
                    'metadata': {**metadata, 'parent_doc_id': doc_id, 'chunk_index': i, 'is_chunk': True},
                } for i, chunk in enumerate(chunks)]
            else:
                new_docs.append({
                    'id': doc_id,
                    'content': doc['content'],
                    'title': doc['title'],
                    'url': doc['url'],
                    'metadata': {**metadata, 'is_chunk': False},
                })
        if not new_docs:
            return 0

        try:
            self._ensure_index()
            vectors = self._embed([doc['content'] for doc in new_docs])
        except Exception as e:
            self.logger.error(f"Error adding documents to index: {e}")
            return 0

        self.index.add(vectors)
        for doc in new_docs:
            self.id_to_doc[doc['id']] = len(self.documents)
            self.documents.append(doc)
        self._save_index()
        self.logger.info(f"Added {len(new_docs)} documents to vector database")
        return len(new_docs)

    def search(self, query: str, limit: Optional[int] = None) -> List[SearchResult]:
        """Perform semantic search"""
        if not query.strip() or not self.documents:
            return []
        limit = limit or self.max_results

        try:
            self._ensure_index()
            scores, indices = self.index.search(self._embed([query]), min(limit, self.index.ntotal))
        except Exception as e:
            self.logger.error(f"Search error: {e}")
            return []

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if 0 <= idx < len(self.documents):
                doc = self.documents[idx]
                content = doc['content']
                results.append(SearchResult(
                    id=doc['id'],
                    content=content[:500] + "..." if len(content) > 500 else content,
                    title=doc['title'],
                    score=float(score),
                    metadata=doc.get('metadata', {}),
                    url=doc['url'],
                ))
        self.logger.info(f"Search for '{query}' returned {len(results)} results")
        return results

    def similarities(self, query: str, texts: List[str]) -> List[float]:
        """Cosine similarity of each text to the query, with the index's embedding model (0 if embedding fails)."""
        if not texts:
            return []
        try:
            vectors = self._embed([query] + texts)
        except Exception as e:
            self.logger.error(f"Scoring failed: {e}")
            return [0.0] * len(texts)
        return [float(score) for score in vectors[1:] @ vectors[0]]
    
    def search_by_filters(self, query: str, filters: Dict, limit: Optional[int] = None) -> List[SearchResult]:
        """Search with metadata filters"""
        matches = [
            r for r in self.search(query, len(self.documents))
            if all(r.metadata.get(key) == value for key, value in filters.items())
        ]
        return matches[:limit] if limit else matches

    def get_document_by_id(self, doc_id: str) -> Optional[Dict]:
        """Retrieve a document by ID"""
        i = self.id_to_doc.get(doc_id)
        return self.documents[i] if i is not None else None

    def get_stats(self) -> Dict:
        """Get database statistics"""
        return {
            'total_documents': len(self.documents),
            'vector_dimension': self.vector_dim,
            'model_name': self.model_name,
            'index_size': self.index.ntotal,
            'last_updated': time.time()
        }

    def rebuild_index(self) -> bool:
        """Re-embed every document and persist."""
        try:
            self._reindex()
        except Exception as e:
            self.logger.error(f"Error rebuilding index: {e}")
            return False
        self._save_index()
        return True

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document from the index (re-embeds the rest)"""
        if doc_id not in self.id_to_doc:
            return False
        del self.documents[self.id_to_doc[doc_id]]
        return self.rebuild_index()

    def clear_index(self):
        """Clear all documents"""
        self.documents = []
        self._reindex()
        self._save_index()
        self.logger.info("Index cleared")
