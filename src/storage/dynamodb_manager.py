"""DynamoDB manager for URL and hash state tracking."""

import boto3
import hashlib
import json
from typing import Optional, Dict, Any
from botocore.exceptions import ClientError


class DynamoDBManager:
    """Manages DynamoDB operations for tracking URL state and hashes."""
    
    def __init__(self, table_name: str, region: str = "us-east-1"):
        """Initialize DynamoDB manager.
        
        Args:
            table_name: Name of the DynamoDB table
            region: AWS region
        """
        self.table_name = table_name
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(table_name)
        
    def get_url_state(self, dataset_name: str, url: str) -> Optional[Dict[str, Any]]:
        """Get state for a URL.
        
        Args:
            dataset_name: Name of the dataset
            url: URL to check
            
        Returns:
            URL state dict or None if not found
        """
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        key = f"{dataset_name}#{url_hash}"
        
        try:
            response = self.table.get_item(
                Key={"key": key}
            )
            if "Item" in response:
                return response["Item"]
            return None
        except ClientError as e:
            raise Exception(f"Failed to get URL state: {e}")
    
    def update_url_state(
        self,
        dataset_name: str,
        url: str,
        content_hash: str,
        s3_key: str,
        status: str = "scraped"
    ) -> None:
        """Update or create URL state.
        
        Args:
            dataset_name: Name of the dataset
            url: URL
            content_hash: SHA-256 hash of content
            s3_key: S3 key where content is stored
            status: Status of the URL
        """
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        key = f"{dataset_name}#{url_hash}"
        
        try:
            self.table.put_item(
                Item={
                    "key": key,
                    "dataset": dataset_name,
                    "url": url,
                    "url_hash": url_hash,
                    "content_hash": content_hash,
                    "s3_key": s3_key,
                    "status": status,
                    "updated_at": self._get_timestamp()
                }
            )
        except ClientError as e:
            raise Exception(f"Failed to update URL state: {e}")
    
    def is_url_processed(self, dataset_name: str, url: str, content_hash: str) -> bool:
        """Check if URL has been processed with same content hash.
        
        Args:
            dataset_name: Name of the dataset
            url: URL to check
            content_hash: Current content hash
            
        Returns:
            True if URL was already processed with same hash
        """
        state = self.get_url_state(dataset_name, url)
        if state and state.get("content_hash") == content_hash:
            return True
        return False
    
    def get_url_by_s3_key(self, dataset_name: str, s3_key: str) -> Optional[Dict[str, Any]]:
        """Get URL state by S3 key.
        
        Args:
            dataset_name: Name of the dataset
            s3_key: S3 key to look up
            
        Returns:
            URL state dict or None if not found
        """
        try:
            # Scan for items with matching dataset and s3_key
            # Note: This is inefficient for large tables - consider using GSI in production
            response = self.table.scan(
                FilterExpression="dataset = :dataset AND s3_key = :s3_key",
                ExpressionAttributeValues={
                    ":dataset": dataset_name,
                    ":s3_key": s3_key
                }
            )
            
            items = response.get("Items", [])
            if items:
                return items[0]
            return None
        except ClientError as e:
            raise Exception(f"Failed to get URL by S3 key: {e}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp as ISO string."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
