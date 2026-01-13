"""Lambda handler for API endpoints."""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from src.api.retrieval_api import RetrievalAPI
from src.api.tv_api import TVAPI
from src.vector.pinecone_manager import PineconeManager
from src.processing.embedder import Embedder


def lambda_handler(event, context):
    """Lambda handler for API endpoints.
    
    Event structure (API Gateway):
    {
        "path": "/retrieval" | "/tv",
        "httpMethod": "GET" | "POST",
        "queryStringParameters": {...},
        "body": "..." (JSON string for POST)
    }
    """
    # Get configuration
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    pinecone_index = os.environ.get("PINECONE_INDEX_NAME")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    s3_bucket = os.environ.get("S3_BUCKET_NAME", "")
    
    if not all([pinecone_api_key, pinecone_index, openai_api_key]):
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Missing required environment variables"})
        }
    
    # Initialize managers
    pinecone_manager = PineconeManager(pinecone_api_key, pinecone_index)
    embedder = Embedder(openai_api_key)
    retrieval_api = RetrievalAPI(pinecone_manager, embedder)
    tv_api = TVAPI(retrieval_api, s3_bucket=s3_bucket if s3_bucket else None)
    
    # Parse request
    path = event.get("path", "")
    method = event.get("httpMethod", "GET")
    
    # Parse query parameters or body
    if method == "GET":
        params = event.get("queryStringParameters") or {}
    else:
        body = event.get("body", "{}")
        params = json.loads(body) if isinstance(body, str) else body
    
    dataset_name = params.get("dataset")
    query = params.get("query") or params.get("q")
    
    if not dataset_name or not query:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Missing dataset or query parameter"})
        }
    
    try:
        if path.endswith("/retrieval"):
            # Standard retrieval API
            top_k = int(params.get("top_k", 5))
            namespace = params.get("namespace", "production")
            
            result = retrieval_api.query(
                dataset_name=dataset_name,
                query_text=query,
                top_k=top_k,
                namespace=namespace
            )
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(result)
            }
        
        elif path.endswith("/tv"):
            # TV-ready API
            use_precomputed = params.get("use_precomputed", "true").lower() == "true"
            
            result = tv_api.get_tv_output(
                dataset_name=dataset_name,
                query_text=query,
                use_precomputed=use_precomputed
            )
            
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(result)
            }
        
        else:
            return {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"error": "Endpoint not found"})
            }
    
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
