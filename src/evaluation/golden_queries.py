"""Golden query management for evaluation."""

import json
import boto3
from typing import List, Dict, Any, Optional
from botocore.exceptions import ClientError


class GoldenQueryManager:
    """Manages golden queries for dataset evaluation."""
    
    def __init__(self, storage_type: str = "dynamodb", table_name: Optional[str] = None, s3_bucket: Optional[str] = None):
        """Initialize golden query manager.
        
        Args:
            storage_type: "dynamodb" or "s3"
            table_name: DynamoDB table name (if using DynamoDB)
            s3_bucket: S3 bucket name (if using S3)
        """
        self.storage_type = storage_type
        
        if storage_type == "dynamodb" and table_name:
            self.dynamodb = boto3.resource("dynamodb")
            self.table = self.dynamodb.Table(table_name)
        elif storage_type == "s3" and s3_bucket:
            self.s3_client = boto3.client("s3")
            self.bucket = s3_bucket
        else:
            # In-memory storage for testing
            self._queries = {}
    
    def get_queries(self, dataset_name: str) -> List[Dict[str, Any]]:
        """Get golden queries for a dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            List of golden query dictionaries
        """
        if self.storage_type == "dynamodb":
            try:
                response = self.table.get_item(
                    Key={"dataset": dataset_name, "type": "golden_queries"}
                )
                if "Item" in response:
                    return json.loads(response["Item"].get("queries", "[]"))
                return []
            except ClientError as e:
                raise Exception(f"Failed to get golden queries: {e}")
        elif self.storage_type == "s3":
            key = f"{dataset_name}/golden_queries.json"
            try:
                response = self.s3_client.get_object(Bucket=self.bucket, Key=key)
                content = response["Body"].read().decode("utf-8")
                return json.loads(content)
            except ClientError as e:
                if e.response["Error"]["Code"] == "NoSuchKey":
                    return []
                raise Exception(f"Failed to get golden queries: {e}")
        else:
            # In-memory
            return self._queries.get(dataset_name, [])
    
    def save_queries(self, dataset_name: str, queries: List[Dict[str, Any]]) -> None:
        """Save golden queries for a dataset.
        
        Args:
            dataset_name: Name of the dataset
            queries: List of golden query dictionaries
        """
        if self.storage_type == "dynamodb":
            try:
                self.table.put_item(
                    Item={
                        "dataset": dataset_name,
                        "type": "golden_queries",
                        "queries": json.dumps(queries)
                    }
                )
            except ClientError as e:
                raise Exception(f"Failed to save golden queries: {e}")
        elif self.storage_type == "s3":
            key = f"{dataset_name}/golden_queries.json"
            try:
                self.s3_client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=json.dumps(queries, indent=2).encode("utf-8"),
                    ContentType="application/json"
                )
            except ClientError as e:
                raise Exception(f"Failed to save golden queries: {e}")
        else:
            # In-memory
            self._queries[dataset_name] = queries
