"""Pinecone vector database manager."""

import hashlib
from typing import List, Dict, Any, Optional
from pinecone import Pinecone, ServerlessSpec
from pinecone.exceptions import PineconeException


class PineconeManager:
    """Manages Pinecone operations for vector storage."""
    
    def __init__(self, api_key: str, index_name: str, environment: str = "us-east-1-aws"):
        """Initialize Pinecone manager.
        
        Args:
            api_key: Pinecone API key
            index_name: Name of the Pinecone index
            environment: Pinecone environment/region
        """
        self.pc = Pinecone(api_key=api_key)
        self.index_name = index_name
        self.index = self.pc.Index(index_name)
        
    def upsert_chunks(
        self,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
        dataset_name: str,
        namespace: str = "staging"
    ) -> int:
        """Upsert chunks with embeddings to Pinecone.
        
        Args:
            chunks: List of chunk dictionaries with text and metadata
            embeddings: List of embedding vectors
            dataset_name: Name of the dataset
            namespace: Pinecone namespace (staging or production)
            
        Returns:
            Number of vectors upserted
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
        
        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            # Generate deterministic ID
            vector_id = self._generate_vector_id(dataset_name, chunk["text"])
            
            vector = {
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "text": chunk["text"],
                    "dataset": dataset_name,
                    "url": chunk.get("url", ""),
                    "title": chunk.get("title", ""),
                    "chunk_index": chunk.get("chunk_index", 0)
                }
            }
            vectors.append(vector)
        
        try:
            # Upsert in batches (Pinecone limit is 100 vectors per request)
            batch_size = 100
            total_upserted = 0
            
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i:i + batch_size]
                self.index.upsert(vectors=batch, namespace=namespace)
                total_upserted += len(batch)
            
            return total_upserted
        except PineconeException as e:
            raise Exception(f"Failed to upsert to Pinecone: {e}")
    
    def query(
        self,
        query_embedding: List[float],
        dataset_name: str,
        top_k: int = 5,
        namespace: str = "staging",
        filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Query Pinecone index.
        
        Args:
            query_embedding: Query embedding vector
            dataset_name: Dataset to filter by
            top_k: Number of results to return
            namespace: Namespace to query
            filter: Optional metadata filter
            
        Returns:
            List of matching chunks with scores
        """
        if filter is None:
            filter = {"dataset": dataset_name}
        else:
            filter["dataset"] = dataset_name
        
        try:
            results = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                namespace=namespace,
                include_metadata=True,
                filter=filter
            )
            
            chunks = []
            for match in results.matches:
                chunks.append({
                    "id": match.id,
                    "score": match.score,
                    "text": match.metadata.get("text", ""),
                    "metadata": match.metadata
                })
            
            return chunks
        except PineconeException as e:
            raise Exception(f"Failed to query Pinecone: {e}")
    
    def _generate_vector_id(self, dataset_name: str, chunk_text: str) -> str:
        """Generate deterministic vector ID.
        
        Args:
            dataset_name: Name of the dataset
            chunk_text: Text content of the chunk
            
        Returns:
            Deterministic vector ID
        """
        # Use hash of dataset + text for deterministic IDs
        content = f"{dataset_name}:{chunk_text}"
        hash_obj = hashlib.sha256(content.encode("utf-8"))
        return hash_obj.hexdigest()[:32]  # Use first 32 chars (Pinecone ID limit)
