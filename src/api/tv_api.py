"""TV-ready API with precomputed outputs."""

from typing import List, Dict, Any, Optional
import json
import boto3
from botocore.exceptions import ClientError
from src.processing.fact_extractor import FactExtractor
from src.api.retrieval_api import RetrievalAPI


class TVAPI:
    """TV-ready API that returns fast, structured, cited output."""
    
    def __init__(
        self,
        retrieval_api: RetrievalAPI,
        s3_bucket: Optional[str] = None,
        fact_extractor: Optional[FactExtractor] = None
    ):
        """Initialize TV API.
        
        Args:
            retrieval_api: Retrieval API instance
            s3_bucket: S3 bucket for storing precomputed outputs
            fact_extractor: Fact extractor instance
        """
        self.retrieval_api = retrieval_api
        self.s3_bucket = s3_bucket
        self.fact_extractor = fact_extractor or FactExtractor()
        self.s3_client = boto3.client("s3") if s3_bucket else None
        
    def get_tv_output(
        self,
        dataset_name: str,
        query_text: str,
        use_precomputed: bool = True
    ) -> Dict[str, Any]:
        """Get TV-ready output for a query.
        
        Args:
            dataset_name: Name of the dataset
            query_text: Query text
            use_precomputed: Whether to use precomputed output if available
            
        Returns:
            TV-ready output with summary, fact cards, and citations
        """
        # Try to get precomputed output
        if use_precomputed and self.s3_bucket:
            precomputed = self._get_precomputed(dataset_name, query_text)
            if precomputed:
                return precomputed
        
        # Generate on-the-fly (fallback)
        return self._generate_tv_output(dataset_name, query_text)
    
    def _get_precomputed(self, dataset_name: str, query_text: str) -> Optional[Dict[str, Any]]:
        """Get precomputed TV output from S3.
        
        Args:
            dataset_name: Name of the dataset
            query_text: Query text
            
        Returns:
            Precomputed output or None
        """
        if not self.s3_bucket:
            return None
        
        # Create deterministic key from query
        import hashlib
        query_hash = hashlib.sha256(query_text.encode()).hexdigest()[:16]
        key = f"{dataset_name}/tv_output/{query_hash}.json"
        
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            return json.loads(content)
        except ClientError:
            return None
    
    def _generate_tv_output(self, dataset_name: str, query_text: str) -> Dict[str, Any]:
        """Generate TV output on-the-fly (fallback).
        
        Args:
            dataset_name: Name of the dataset
            query_text: Query text
            
        Returns:
            TV-ready output
        """
        # Get retrieval results
        retrieval_results = self.retrieval_api.query(
            dataset_name=dataset_name,
            query_text=query_text,
            top_k=5,
            namespace="production"
        )
        
        # Extract facts from top results
        all_facts = []
        citations = []
        
        for result in retrieval_results["results"]:
            text = result["text"]
            metadata = result["metadata"]
            
            # Extract facts
            facts = self.fact_extractor.extract_facts(text, max_facts=3)
            fact_cards = self.fact_extractor.create_fact_cards(facts, metadata)
            all_facts.extend(fact_cards)
            
            # Collect citations
            citation = result["citation"]
            if citation["url"] and citation["url"] not in [c["url"] for c in citations]:
                citations.append(citation)
        
        # Create summary (simple concatenation of top facts)
        summary_text = ". ".join([fact["fact"] for fact in all_facts[:3]])
        if len(summary_text) > 200:
            summary_text = summary_text[:200] + "..."
        
        # Generate handoff URL
        handoff_url = f"/dataset/{dataset_name}/query?q={query_text}"
        
        return {
            "query": query_text,
            "summary": summary_text,
            "fact_cards": all_facts[:10],  # Limit to 10 facts
            "citations": citations,
            "handoff_url": handoff_url,
            "qr_url": handoff_url  # Same URL for QR code
        }
    
    def store_precomputed(
        self,
        dataset_name: str,
        query_text: str,
        tv_output: Dict[str, Any]
    ) -> None:
        """Store precomputed TV output in S3.
        
        Args:
            dataset_name: Name of the dataset
            query_text: Query text
            tv_output: TV output to store
        """
        if not self.s3_bucket:
            return
        
        import hashlib
        query_hash = hashlib.sha256(query_text.encode()).hexdigest()[:16]
        key = f"{dataset_name}/tv_output/{query_hash}.json"
        
        try:
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=key,
                Body=json.dumps(tv_output, indent=2).encode("utf-8"),
                ContentType="application/json"
            )
        except ClientError as e:
            raise Exception(f"Failed to store precomputed output: {e}")
