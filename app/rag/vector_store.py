"""FAISS-based vector store implementation."""
import faiss
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict, Any
import json
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class FAISSVectorStore:
    """FAISS-based vector store for embeddings."""
    
    def __init__(self, embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2", 
                 index_path: str = "./data/faiss_index",
                 metadata_path: str = "./data/metadata.json"):
        self.embedding_model = SentenceTransformer(embedding_model)
        self.index = None
        self.chunks = []
        self.metadata = []
        self.index_path = index_path
        self.metadata_path = metadata_path
        
        # Try to load existing index
        self._load_index()
    
    def _ensure_dir_exists(self):
        """Ensure data directory exists."""
        Path(self.index_path).parent.mkdir(parents=True, exist_ok=True)
    
    def _load_index(self):
        """Load existing FAISS index if available."""
        try:
            index_file = Path(self.index_path + ".faiss")
            metadata_file = Path(self.metadata_path)
            
            if index_file.exists() and metadata_file.exists():
                self.index = faiss.read_index(str(index_file))
                with open(metadata_file, 'r') as f:
                    self.metadata = json.load(f)
                logger.info(f"Loaded existing FAISS index with {len(self.metadata)} chunks")
            else:
                logger.info("No existing FAISS index found")
        except Exception as e:
            logger.warning(f"Failed to load existing index: {str(e)}")
    
    def add_chunks(self, chunks: List[Dict[str, Any]]):
        """
        Add text chunks to the vector store.
        
        Args:
            chunks: List of chunk dictionaries with 'content' and 'metadata'
        """
        if not chunks:
            return
        
        self._ensure_dir_exists()
        
        # Extract texts and generate embeddings
        texts = [chunk['content'] for chunk in chunks]
        embeddings = self.embedding_model.encode(texts)
        embeddings = np.array(embeddings).astype('float32')
        
        # Initialize or update FAISS index
        if self.index is None:
            # Create new index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
        
        # Add embeddings
        self.index.add(embeddings)
        
        # Store metadata
        for chunk in chunks:
            self.metadata.append({
                'chunk_id': chunk['chunk_id'],
                'content': chunk['content'],
                'metadata': chunk['metadata']
            })
        
        logger.info(f"Added {len(chunks)} chunks to FAISS index")
        
        # Save index and metadata
        self._save_index()
    
    def _save_index(self):
        """Save FAISS index and metadata to disk."""
        try:
            self._ensure_dir_exists()
            faiss.write_index(self.index, str(Path(self.index_path + ".faiss")))
            with open(self.metadata_path, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info("Saved FAISS index and metadata")
        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}")
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search for similar chunks using the query.
        
        Args:
            query: Query text
            top_k: Number of results to return
            
        Returns:
            List of most similar chunks with distances
        """
        if self.index is None or len(self.metadata) == 0:
            logger.warning("FAISS index is empty")
            return []
        
        # Embed the query
        query_embedding = self.embedding_model.encode([query])
        query_embedding = np.array(query_embedding).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_embedding, min(top_k, len(self.metadata)))
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0:  # Valid index
                metadata_entry = self.metadata[idx]
                results.append({
                    'chunk_id': metadata_entry['chunk_id'],
                    'content': metadata_entry['content'],
                    'distance': float(dist),
                    'similarity_score': 1.0 / (1.0 + float(dist)),  # Convert distance to similarity
                    'metadata': metadata_entry['metadata']
                })
        
        logger.info(f"Retrieved {len(results)} chunks for query")
        return results
    
    def clear(self):
        """Clear the index."""
        self.index = None
        self.metadata = []
        logger.info("Cleared FAISS index")
