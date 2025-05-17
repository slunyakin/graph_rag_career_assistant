# Document Embedding Component Documentation

This document provides detailed technical information about the document embedding functionality in AskCareer. For general project information, please refer to the main [README.md](../README.md) in the project root.

## Overview

This component processes markdown documents from the `data` directory and creates embeddings using FAISS vector store.

## Setup

1. Install requirements:
```bash
pip install -r requirements.txt
```

2. Ensure your data directory structure is correct:
```
data/
├── roles/          # Role descriptions
├── skills/         # Skill descriptions
└── learning_paths/ # Learning path documents
```

## Usage

The script supports two modes of operation:

### Full Processing
Processes all documents from scratch:
```bash
python scripts/embed_documents.py
```

### Incremental Processing
Only processes new or modified documents:
```bash
python scripts/embed_documents.py --incremental
```

## Features

- **Full Processing**:
  - Creates a backup of existing vector store
  - Processes all documents from scratch
  - Creates new vector store with all documents
  - Updates metadata with complete statistics

- **Incremental Processing**:
  - Only processes new or modified documents
  - Preserves existing embeddings
  - Updates vector store with new content
  - Maintains document history

## Output

The script creates a vector store in `rag/vector_store/` with:
- FAISS index files
- `metadata.json` with processing statistics
- `metadata_summary.txt` with human-readable summary
- Backup directory for previous versions

## Notes

- Full processing is recommended for first run or when you want to rebuild the entire index
- Incremental processing is faster and recommended for regular updates
- Backups are automatically created before full processing
- The script uses the `sentence-transformers/all-MiniLM-L6-v2` model for embeddings
- Documents are split into chunks of 2000 characters with 400 character overlap
- Markdown headers are preserved in the chunking process 