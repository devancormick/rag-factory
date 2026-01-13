"""Lambda handler for promotion."""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from src.promotion.promoter import Promoter
from src.evaluation.evaluator import Evaluator
from src.evaluation.golden_queries import GoldenQueryManager
from src.vector.pinecone_manager import PineconeManager
from src.processing.embedder import Embedder


def lambda_handler(event, context):
    """Lambda handler for promotion.
    
    Event structure:
    {
        "dataset_name": "my_dataset"
    }
    """
    # Get configuration
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    pinecone_index = os.environ.get("PINECONE_INDEX_NAME")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    dynamodb_table = os.environ.get("DYNAMODB_TABLE_NAME", "")
    
    if not all([pinecone_api_key, pinecone_index, openai_api_key]):
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Missing required environment variables"})
        }
    
    # Initialize managers
    pinecone_manager = PineconeManager(pinecone_api_key, pinecone_index)
    embedder = Embedder(openai_api_key)
    golden_query_manager = GoldenQueryManager(
        storage_type="dynamodb" if dynamodb_table else "memory",
        table_name=dynamodb_table
    )
    evaluator = Evaluator(golden_query_manager)
    promoter = Promoter(pinecone_manager, evaluator)
    
    dataset_name = event.get("dataset_name")
    if not dataset_name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing dataset_name"})
        }
    
    def query_embedding_func(query_text: str):
        """Helper to get query embedding."""
        return embedder.generate_embedding(query_text)
    
    try:
        result = promoter.promote_dataset(
            dataset_name=dataset_name,
            query_embedding_func=query_embedding_func
        )
        
        status_code = 200 if result.get("success") else 400
        return {
            "statusCode": status_code,
            "body": json.dumps(result)
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }
