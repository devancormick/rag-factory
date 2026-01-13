"""Lambda handler for scraping harvester."""

import json
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from src.scraper.crawler import Crawler
from src.scraper.sitemap_parser import SitemapParser
from src.storage.s3_manager import S3Manager
from src.storage.dynamodb_manager import DynamoDBManager


def lambda_handler(event, context):
    """Lambda handler for scraping harvester.
    
    Event structure:
    {
        "dataset_name": "my_dataset",
        "source_type": "sitemap" | "url" | "urls",
        "source": "https://example.com/sitemap.xml" | "https://example.com" | ["url1", "url2"],
        "base_url": "https://example.com"
    }
    """
    # Get configuration from environment
    s3_bucket = os.environ.get("S3_BUCKET_NAME")
    dynamodb_table = os.environ.get("DYNAMODB_TABLE_NAME")
    region = os.environ.get("AWS_REGION", "us-east-1")
    
    if not s3_bucket or not dynamodb_table:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": "Missing S3_BUCKET_NAME or DYNAMODB_TABLE_NAME"})
        }
    
    # Initialize managers
    s3_manager = S3Manager(s3_bucket, region)
    dynamodb_manager = DynamoDBManager(dynamodb_table, region)
    
    # Parse event
    dataset_name = event.get("dataset_name")
    source_type = event.get("source_type", "url")
    source = event.get("source")
    base_url = event.get("base_url", source if isinstance(source, str) else "")
    
    if not dataset_name or not source:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "Missing dataset_name or source"})
        }
    
    # Initialize crawler
    crawler = Crawler(base_url=base_url)
    
    # Get URLs to process
    urls_to_process = set()
    
    if source_type == "sitemap":
        sitemap_parser = SitemapParser()
        urls_to_process = sitemap_parser.parse_sitemap(source)
        urls_to_process = sitemap_parser.filter_same_domain(urls_to_process, base_url)
    elif source_type == "url":
        urls_to_process = {source}
    elif source_type == "urls":
        urls_to_process = set(source)
    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Invalid source_type: {source_type}"})
        }
    
    # Process URLs
    processed = 0
    skipped = 0
    failed = 0
    
    for url in urls_to_process:
        try:
            # Check if already processed
            html_content = crawler.fetch_url(url)
            if not html_content:
                failed += 1
                continue
            
            content_hash = crawler.get_content_hash(html_content)
            
            if dynamodb_manager.is_url_processed(dataset_name, url, content_hash):
                skipped += 1
                continue
            
            # Store in S3
            s3_key = s3_manager.store_html(dataset_name, url, html_content)
            
            # Update DynamoDB state
            dynamodb_manager.update_url_state(
                dataset_name=dataset_name,
                url=url,
                content_hash=content_hash,
                s3_key=s3_key,
                status="scraped"
            )
            
            processed += 1
            
        except Exception as e:
            failed += 1
            print(f"Error processing {url}: {e}")
    
    return {
        "statusCode": 200,
        "body": json.dumps({
            "dataset_name": dataset_name,
            "processed": processed,
            "skipped": skipped,
            "failed": failed,
            "total": len(urls_to_process)
        })
    }
