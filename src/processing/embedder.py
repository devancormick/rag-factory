"""Embedding generation using OpenAI."""

import hashlib
from typing import List, Dict, Any
from openai import OpenAI


class Embedder:
    """Generates embeddings using OpenAI text-embedding-3-small."""
    
    def __init__(self, api_key: str):
        """Initialize embedder.
        
        Args:
            api_key: OpenAI API key
        """
        self.client = OpenAI(api_key=api_key)
        self.model = "text-embedding-3-small"
        
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            raise Exception(f"Failed to generate embeddings: {e}")
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        embeddings = self.generate_embeddings([text])
        return embeddings[0]
    
    @staticmethod
    def compute_text_hash(text: str) -> str:
        """Compute SHA-256 hash of text.
        
        Args:
            text: Text to hash
            
        Returns:
            Hex digest of hash
        """
        return hashlib.sha256(text.encode("utf-8")).hexdigest()
