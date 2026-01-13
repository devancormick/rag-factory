"""S3 storage manager for raw HTML content."""

import boto3
import hashlib
from typing import Optional
from botocore.exceptions import ClientError


class S3Manager:
    """Manages S3 operations for storing raw scraped content."""
    
    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        """Initialize S3 manager.
        
        Args:
            bucket_name: Name of the S3 bucket
            region: AWS region
        """
        self.bucket_name = bucket_name
        self.s3_client = boto3.client("s3", region_name=region)
        
    def store_html(self, dataset_name: str, url: str, html_content: str) -> str:
        """Store HTML content in S3 with dataset-based path.
        
        Args:
            dataset_name: Name of the dataset
            url: Source URL
            html_content: Raw HTML content
            
        Returns:
            S3 key path
        """
        # Create deterministic key based on URL hash
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        key = f"{dataset_name}/raw/{url_hash}.html"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=html_content.encode("utf-8"),
                ContentType="text/html",
                Metadata={"url": url, "dataset": dataset_name}
            )
            return key
        except ClientError as e:
            raise Exception(f"Failed to store HTML in S3: {e}")
    
    def get_html(self, key: str) -> Optional[str]:
        """Retrieve HTML content from S3.
        
        Args:
            key: S3 key path
            
        Returns:
            HTML content or None if not found
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            return response["Body"].read().decode("utf-8")
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                return None
            raise Exception(f"Failed to retrieve HTML from S3: {e}")
    
    def object_exists(self, key: str) -> bool:
        """Check if object exists in S3.
        
        Args:
            key: S3 key path
            
        Returns:
            True if object exists
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except ClientError:
            return False
