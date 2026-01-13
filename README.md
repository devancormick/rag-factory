# RAG Factory

A production-grade data ingestion pipeline for RAG (Retrieval-Augmented Generation) systems.

## Overview

RAG Factory is a reusable data ingestion system that allows operators to process web content end-to-end:
- Scrape content from URLs or sitemaps
- Clean and chunk content using document structure
- Generate embeddings and store in Pinecone
- Evaluate and promote data to production
- Expose APIs for retrieval and TV-ready output

## Architecture

- **Cloud**: AWS (S3, Lambda, DynamoDB, Fargate if needed)
- **Vector Database**: Pinecone Serverless
- **Embeddings**: OpenAI text-embedding-3-small
- **UI**: Streamlit
- **Infrastructure**: AWS SAM

## Quick Start

### Prerequisites

- Python 3.10+
- AWS account with appropriate permissions
- Pinecone account
- OpenAI API key

### Installation

```bash
pip install -r requirements.txt
```

### Configuration

Set environment variables:

```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_REGION=us-east-1
export PINECONE_API_KEY=your_key
export OPENAI_API_KEY=your_key
export PINECONE_INDEX_NAME=your_index
export S3_BUCKET_NAME=your_bucket
export DYNAMODB_TABLE_NAME=your_table
```

### Running the UI

```bash
streamlit run ui/app.py
```

## Project Structure

```
rag-factory/
├── infrastructure/    # AWS SAM templates
├── lambda/           # Lambda function handlers
├── src/              # Core library code
├── ui/               # Streamlit interface
├── tests/            # Test suite
└── scripts/          # Utility scripts
```

## Development

See PLAN.md for detailed implementation roadmap.

## License

Proprietary
