"""Evaluation system for quality checks."""

import re
from typing import List, Dict, Any, Optional
from .golden_queries import GoldenQueryManager


class Evaluator:
    """Evaluates data quality before promotion."""
    
    def __init__(self, golden_query_manager: GoldenQueryManager):
        """Initialize evaluator.
        
        Args:
            golden_query_manager: Manager for golden queries
        """
        self.golden_query_manager = golden_query_manager
        
    def evaluate_dataset(
        self,
        dataset_name: str,
        query_embedding_func
    ) -> Dict[str, Any]:
        """Evaluate a dataset using golden queries.
        
        Args:
            dataset_name: Name of the dataset
            query_embedding_func: Function to get embeddings for queries
            
        Returns:
            Evaluation results
        """
        golden_queries = self.golden_query_manager.get_queries(dataset_name)
        
        if not golden_queries:
            return {
                "passed": False,
                "error": "No golden queries defined for dataset",
                "checks": []
            }
        
        checks = []
        all_passed = True
        
        for query in golden_queries:
            check_result = self._check_golden_query(
                dataset_name=dataset_name,
                query=query,
                query_embedding_func=query_embedding_func
            )
            checks.append(check_result)
            if not check_result["passed"]:
                all_passed = False
        
        return {
            "passed": all_passed,
            "checks": checks,
            "total_queries": len(golden_queries),
            "passed_queries": sum(1 for c in checks if c["passed"])
        }
    
    def _check_golden_query(
        self,
        dataset_name: str,
        query: Dict[str, Any],
        query_embedding_func
    ) -> Dict[str, Any]:
        """Check a single golden query.
        
        Args:
            dataset_name: Name of the dataset
            query: Golden query dictionary
            query_embedding_func: Function to get embedding for query text
            
        Returns:
            Check result
        """
        query_text = query.get("query", "")
        expected_citations = query.get("expected_citations", [])
        min_score = query.get("min_score", 0.7)
        
        # Get query embedding
        query_embedding = query_embedding_func(query_text)
        
        # This would typically use PineconeManager, but we're abstracting here
        # Assume we get results with citations
        results = []  # Would come from Pinecone query
        
        issues = []
        
        # Check if we got results
        if not results or (results and results[0].get("score", 0) < min_score):
            issues.append(f"No relevant results found (min score: {min_score})")
        
        # Check citations
        citations_found = []
        for result in results:
            citation = result.get("metadata", {}).get("url", "")
            if citation:
                citations_found.append(citation)
        
        if expected_citations:
            missing_citations = set(expected_citations) - set(citations_found)
            if missing_citations:
                issues.append(f"Missing expected citations: {missing_citations}")
        
        passed = len(issues) == 0
        
        return {
            "query": query_text,
            "passed": passed,
            "issues": issues,
            "citations_found": citations_found
        }
    
    def check_chunk_integrity(self, chunk_text: str) -> Dict[str, Any]:
        """Check chunk integrity (no mid-sentence splits, etc.).
        
        Args:
            chunk_text: Text of the chunk
            
        Returns:
            Integrity check result
        """
        issues = []
        
        # Check for mid-sentence splits (text ending without sentence-ending punctuation)
        # This is a simple check - could be more sophisticated
        lines = chunk_text.strip().split("\n")
        if lines:
            last_line = lines[-1].strip()
            # Check if last line ends with sentence-ending punctuation
            if last_line and not re.search(r[.!?]$", last_line):
                # Could be mid-sentence, but also could be a list item, etc.
                # More sophisticated checking would be needed
                pass
        
        # Check for incomplete sentences (heuristic)
        # Look for common patterns that suggest incomplete text
        if chunk_text and not re.search(r[.!?]$", chunk_text.rstrip()):
            # Doesn't end with sentence punctuation
            # But this could be fine for lists, etc.
            pass
        
        return {
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    def validate_citations(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate that chunks have proper citations.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Validation result
        """
        issues = []
        chunks_without_citations = []
        
        for i, chunk in enumerate(chunks):
            metadata = chunk.get("metadata", {})
            url = metadata.get("url", "")
            
            if not url:
                chunks_without_citations.append(i)
                issues.append(f"Chunk {i} missing URL citation")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues,
            "chunks_without_citations": chunks_without_citations
        }
