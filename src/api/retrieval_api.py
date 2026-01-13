"""Standard retrieval API."""

from typing import List, Dict, Any, Optional
from src.vector.pinecone_manager import PineconeManager
from src.processing.embedder import Embedder


class RetrievalAPI:
    """Standard retrieval API for web or LLM use."""
    
    def __init__(self, pinecone_manager: PineconeManager, embedder: Embedder):
        """Initialize retrieval API.
        
        Args:
            pinecone_manager: Pinecone manager instance
            embedder: Embedder instance
        """
        self.pinecone_manager = pinecone_manager
        self.embedder = embedder
        
    def query(
        self,
        dataset_name: str,
        query_text: str,
        top_k: int = 5,
        namespace: str = "production"
    ) -> Dict[str, Any]:
        """Query the retrieval API.
        
        Args:
            dataset_name: Name of the dataset
            query_text: Query text
            top_k: Number of results to return
            namespace: Namespace to query (staging or production)
            
        Returns:
            Query results with chunks, metadata, and citations
        """
        # Generate query embedding
        query_embedding = self.embedder.generate_embedding(query_text)
        
        # Query Pinecone
        results = self.pinecone_manager.query(
            query_embedding=query_embedding,
            dataset_name=dataset_name,
            top_k=top_k,
            namespace=namespace
        )
        
        # Format results
        chunks = []
        for result in results:
            chunk = {
                "text": result["text"],
                "score": result["score"],
                "metadata": result["metadata"],
                "citation": {
                    "url": result["metadata"].get("url", ""),
                    "title": result["metadata"].get("title", "")
                }
            }
            chunks.append(chunk)
        
        return {
            "query": query_text,
            "dataset": dataset_name,
            "results": chunks,
            "count": len(chunks)
        }
