"""Lambda handler for processing and chunking."""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from src.storage.s3_manager import S3Manager
from src.storage.dynamodb_manager import DynamoDBManager
from src.processing.cleaner import TextCleaner
from src.processing.chunker import StructureAwareChunker
from src.processing.embedder import Embedder
from src.vector.pinecone_manager import PineconeManager


def lambda_handler(event, context):
    """Lambda handler for processing and chunking.
    
    Event structure:
    {
        "dataset_name": "my_dataset",
        "s3_keys": ["dataset/raw/abc123.html", ...]  # Optional, if not provided, process all scraped URLs
    }
    """
    # Get configuration from environment
    s3_bucket = os.environ.get("S3_BUCKET_NAME")
    dynamodb_table = os.environ.get("DYNAMODB_TABLE_NAME")
    pinecone_api_key = os.environ.get("PINECONE_API_KEY")
    pinecone_index = os.environ.get("PINECONE_INDEX_NAME")
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    region = os.environ.get("AWS_REGION", "us-east-1")
    
    if not all([s3_bucket, dynamodb_table, pinecone_api_key, pinecone_index, openai_api_key]):
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Missing required environment variables"})
        }
    
    # Initialize managers
    s3_manager = S3Manager(s3_bucket, region)
    dynamodb_manager = DynamoDBManager(dynamodb_table, region)
    cleaner = TextCleaner()
    chunker = StructureAwareChunker()
    embedder = Embedder(openai_api_key)
    pinecone_manager = PineconeManager(pinecone_api_key, pinecone_index)
    
    dataset_name = event.get("dataset_name")
    if not dataset_name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing dataset_name"})
        }
    
    # Get S3 keys to process
    s3_keys = event.get("s3_keys", [])
    
    if not s3_keys:
        # If no keys provided, we'd need to scan DynamoDB for scraped URLs
        # For now, return error suggesting keys be provided
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "s3_keys required"})
        }
    
    processed = 0
    skipped = 0
    failed = 0
    total_chunks = 0
    
    for s3_key in s3_keys:
        try:
            # Get HTML from S3
            html_content = s3_manager.get_html(s3_key)
            if not html_content:
                failed += 1
                continue
            
            # Get URL from DynamoDB state
            # Extract URL hash from S3 key (format: dataset/raw/{hash}.html)
            url_hash = s3_key.split("/")[-1].replace(".html", "")
            # We'd need to query DynamoDB by s3_key to get URL
            # For simplicity, assume we have URL in metadata or event
            url = event.get("url_map", {}).get(s3_key, "")
            
            # Clean text
            cleaned_text = cleaner.clean_html(html_content)
            text_hash = embedder.compute_text_hash(cleaned_text)
            
            # Check if already processed with same hash
            state = dynamodb_manager.get_url_state(dataset_name, url)
            if state and state.get("content_hash") == text_hash and state.get("status") == "processed":
                skipped += 1
                continue
            
            # Extract metadata
            metadata = cleaner.extract_metadata(html_content, url)
            
            # Chunk text
            chunks = chunker.chunk_text(cleaned_text, metadata)
            
            # Generate embeddings
            chunk_texts = [chunk["text"] for chunk in chunks]
            embeddings = embedder.generate_embeddings(chunk_texts)
            
            # Add chunk indices
            for i, chunk in enumerate(chunks):
                chunk["chunk_index"] = i
            
            # Upsert to Pinecone staging
            upserted = pinecone_manager.upsert_chunks(
                chunks=chunks,
                embeddings=embeddings,
                dataset_name=dataset_name,
                namespace="staging"
            )
            
            # Update DynamoDB state
            dynamodb_manager.update_url_state(
                dataset_name=dataset_name,
                url=url,
                content_hash=text_hash,
                s3_key=s3_key,
                status="processed"
            )
            
            processed += 1
            total_chunks += len(chunks)
            
        except Exception as e:
            failed += 1
            print(f"Error processing {s3_key}: {e}")
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "dataset_name": dataset_name,
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "total_chunks": total_chunks
        })
    }
