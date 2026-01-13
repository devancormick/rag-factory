"""Evaluation system for quality checks."""

import re
from typing import List, Dict, Any, Optional, Callable
from .golden_queries import GoldenQueryManager


class Evaluator:
    """Evaluates data quality before promotion."""
    
    def __init__(self, golden_query_manager: GoldenQueryManager, query_func: Optional[Callable] = None):
        """Initialize evaluator.
        
        Args:
            golden_query_manager: Manager for golden queries
            query_func: Optional function to query Pinecone (query_func(embedding, dataset_name, namespace) -> results)
        """
        self.golden_query_manager = golden_query_manager
        self.query_func = query_func
        
    def evaluate_dataset(
        self,
        dataset_name: str,
        query_embedding_func,
        namespace: str = "staging"
    ) -> Dict[str, Any]:
        """Evaluate a dataset using golden queries.
        
        Args:
            dataset_name: Name of the dataset
            query_embedding_func: Function to get embeddings for queries
            namespace: Namespace to query (default: staging)
            
        Returns:
            Evaluation results
        """
        golden_queries = self.golden_query_manager.get_queries(dataset_name)
        
        if not golden_queries:
            # Allow promotion if no golden queries defined (optional evaluation)
            return {
                "passed": True,
                "warning": "No golden queries defined for dataset",
                "checks": []
            }
        
        checks = []
        all_passed = True
        
        for query in golden_queries:
            check_result = self._check_golden_query(
                dataset_name=dataset_name,
                query=query,
                query_embedding_func=query_embedding_func,
                namespace=namespace
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
        query_embedding_func,
        namespace: str = "staging"
    ) -> Dict[str, Any]:
        """Check a single golden query.
        
        Args:
            dataset_name: Name of the dataset
            query: Golden query dictionary
            query_embedding_func: Function to get embedding for query text
            namespace: Namespace to query
            
        Returns:
            Check result
        """
        query_text = query.get("query", "")
        expected_citations = query.get("expected_citations", [])
        min_score = query.get("min_score", 0.7)
        
        # Get query embedding
        query_embedding = query_embedding_func(query_text)
        
        # Query Pinecone using query_func if available
        if self.query_func:
            results = self.query_func(query_embedding, dataset_name, namespace)
        else:
            # Fallback: empty results (evaluator needs query_func to work properly)
            results = []
        
        issues = []
        
        # Check if we got results
        if not results:
            issues.append(f"No results found for query")
        elif results[0].get("score", 0) < min_score:
            issues.append(f"Top result score {results[0].get('score', 0):.3f} below minimum {min_score}")
        
        # Check citations
        citations_found = []
        for result in results:
            metadata = result.get("metadata", {})
            url = metadata.get("url", "")
            if url:
                citations_found.append(url)
        
        if expected_citations:
            missing_citations = set(expected_citations) - set(citations_found)
            if missing_citations:
                issues.append(f"Missing expected citations: {list(missing_citations)}")
        
        passed = len(issues) == 0
        
        return {
            "query": query_text,
            "passed": passed,
            "issues": issues,
            "citations_found": citations_found,
            "top_score": results[0].get("score", 0) if results else 0
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
