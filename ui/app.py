"""Streamlit operator interface for RAG Factory."""

import streamlit as st
import os
import json
from typing import Dict, Any, Optional
import boto3
from datetime import datetime

# Add parent directory to path for imports
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../"))

from src.storage.dynamodb_manager import DynamoDBManager
from src.storage.s3_manager import S3Manager
from src.vector.pinecone_manager import PineconeManager
from src.api.retrieval_api import RetrievalAPI
from src.processing.embedder import Embedder


# Page configuration
st.set_page_config(
    page_title="RAG Factory",
    page_icon="🏭",
    layout="wide"
)

# Initialize session state
if "datasets" not in st.session_state:
    st.session_state.datasets = []


def get_config() -> Dict[str, str]:
    """Get configuration from environment or user input."""
    config = {}
    
    # Try to get from environment first
    config["s3_bucket"] = os.environ.get("S3_BUCKET_NAME", "")
    config["dynamodb_table"] = os.environ.get("DYNAMODB_TABLE_NAME", "")
    config["pinecone_api_key"] = os.environ.get("PINECONE_API_KEY", "")
    config["pinecone_index"] = os.environ.get("PINECONE_INDEX_NAME", "")
    config["openai_api_key"] = os.environ.get("OPENAI_API_KEY", "")
    config["region"] = os.environ.get("AWS_REGION", "us-east-1")
    
    return config


def main():
    """Main application."""
    st.title("🏭 RAG Factory")
    st.markdown("Production-grade data ingestion pipeline")
    
    # Configuration section (collapsible)
    with st.expander("⚙️ Configuration", expanded=False):
        config = get_config()
        
        if not all([config["s3_bucket"], config["dynamodb_table"], config["pinecone_api_key"]]):
            st.warning("⚠️ Please set environment variables or configure below")
            
            config["s3_bucket"] = st.text_input("S3 Bucket Name", value=config["s3_bucket"])
            config["dynamodb_table"] = st.text_input("DynamoDB Table Name", value=config["dynamodb_table"])
            config["pinecone_api_key"] = st.text_input("Pinecone API Key", value=config["pinecone_api_key"], type="password")
            config["pinecone_index"] = st.text_input("Pinecone Index Name", value=config["pinecone_index"])
            config["openai_api_key"] = st.text_input("OpenAI API Key", value=config["openai_api_key"], type="password")
            config["region"] = st.text_input("AWS Region", value=config["region"])
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Datasets", "🔄 Run Job", "📈 Status", "🔍 Preview"])
    
    with tab1:
        show_datasets_tab(config)
    
    with tab2:
        show_run_job_tab(config)
    
    with tab3:
        show_status_tab(config)
    
    with tab4:
        show_preview_tab(config)


def show_datasets_tab(config: Dict[str, str]):
    """Show datasets management tab."""
    st.header("📊 Dataset Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Create New Dataset")
        dataset_name = st.text_input("Dataset Name", placeholder="my_dataset")
        
        if st.button("Create Dataset", type="primary"):
            if dataset_name:
                if dataset_name not in st.session_state.datasets:
                    st.session_state.datasets.append(dataset_name)
                    st.success(f"✅ Dataset '{dataset_name}' created")
                else:
                    st.error(f"❌ Dataset '{dataset_name}' already exists")
            else:
                st.error("❌ Please enter a dataset name")
    
    with col2:
        st.subheader("Existing Datasets")
        if st.session_state.datasets:
            for dataset in st.session_state.datasets:
                st.write(f"• {dataset}")
        else:
            st.info("No datasets created yet")


def show_run_job_tab(config: Dict[str, str]):
    """Show job submission tab."""
    st.header("🔄 Run Ingestion Job")
    
    dataset_name = st.selectbox(
        "Select Dataset",
        options=st.session_state.datasets if st.session_state.datasets else [""],
        help="Create a dataset first if none exist"
    )
    
    if not dataset_name:
        st.warning("⚠️ Please create a dataset first")
        return
    
    source_type = st.radio(
        "Source Type",
        options=["url", "sitemap", "urls"],
        help="Select the type of source to process"
    )
    
    if source_type == "url":
        source = st.text_input("URL", placeholder="https://example.com")
    elif source_type == "sitemap":
        source = st.text_input("Sitemap URL", placeholder="https://example.com/sitemap.xml")
    else:
        source = st.text_area("URLs (one per line)", placeholder="https://example.com/page1\nhttps://example.com/page2")
        if source:
            source = [url.strip() for url in source.split("\n") if url.strip()]
    
    base_url = st.text_input("Base URL (for same-domain filtering)", placeholder="https://example.com")
    
    if st.button("🚀 Run Job", type="primary"):
        if source and base_url:
            with st.spinner("Running job..."):
                try:
                    # This would trigger the Lambda function in production
                    # For now, show a placeholder
                    st.info("⚠️ Job submission not fully integrated - this would trigger the scraper Lambda")
                    st.json({
                        "dataset_name": dataset_name,
                        "source_type": source_type,
                        "source": source if source_type != "urls" else source[:3] + ["..."],
                        "base_url": base_url,
                        "status": "submitted"
                    })
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        else:
            st.error("❌ Please provide source and base URL")


def show_status_tab(config: Dict[str, str]):
    """Show job status and logs tab."""
    st.header("📈 Job Status & Logs")
    
    dataset_name = st.selectbox(
        "Select Dataset",
        options=st.session_state.datasets if st.session_state.datasets else [""],
        key="status_dataset"
    )
    
    if not dataset_name:
        st.info("Select a dataset to view status")
        return
    
    # Placeholder for status display
    st.subheader("Recent Jobs")
    
    # This would query DynamoDB for job status in production
    st.info("⚠️ Status tracking not fully integrated - would show job status from DynamoDB")
    
    # Mock status display
    status_data = {
        "dataset": dataset_name,
        "last_run": datetime.now().isoformat(),
        "status": "completed",
        "processed": 0,
        "skipped": 0,
        "failed": 0
    }
    
    st.json(status_data)
    
    # Logs section
    st.subheader("Logs")
    st.text_area("Log Output", value="Logs would appear here...", height=200, disabled=True)


def show_preview_tab(config: Dict[str, str]):
    """Show chunk and citation preview tab."""
    st.header("🔍 Preview Chunks & Citations")
    
    dataset_name = st.selectbox(
        "Select Dataset",
        options=st.session_state.datasets if st.session_state.datasets else [""],
        key="preview_dataset"
    )
    
    if not dataset_name:
        st.info("Select a dataset to preview")
        return
    
    # Query interface
    st.subheader("Test Query")
    query_text = st.text_input("Query", placeholder="Enter a query to test retrieval")
    
    if st.button("🔍 Search", type="primary") and query_text:
        with st.spinner("Searching..."):
            try:
                # This would use the retrieval API in production
                st.info("⚠️ Preview not fully integrated - would query Pinecone via retrieval API")
                
                # Mock results
                mock_results = {
                    "query": query_text,
                    "dataset": dataset_name,
                    "results": [
                        {
                            "text": "Sample chunk text would appear here...",
                            "score": 0.85,
                            "citation": {
                                "url": "https://example.com/page",
                                "title": "Example Page"
                            }
                        }
                    ]
                }
                st.json(mock_results)
            except Exception as e:
                st.error(f"❌ Error: {e}")


if __name__ == "__main__":
    main()
