import os
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Set
import numpy as np
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter, MarkdownHeaderTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.document_loaders import DirectoryLoader, TextLoader
from langchain.schema import Document
import datetime
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('embedding.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
VECTOR_STORE_DIR = ROOT_DIR / "rag" / "vector_store"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 400

# Markdown header patterns to split on
HEADERS_TO_SPLIT_ON = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

class DocumentEmbedder:
    def __init__(self):
        self.embeddings = None
        self.vector_store = None
        self.metadata_file = VECTOR_STORE_DIR / "metadata.json"
        self.backup_dir = VECTOR_STORE_DIR / "backups"
        
    def initialize_embeddings(self):
        """Initialize the embedding model."""
        try:
            logger.info("Initializing embedding model...")
            self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
            logger.info("Embedding model initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            raise

    def _create_backup(self) -> None:
        """Create a backup of the current vector store."""
        if not VECTOR_STORE_DIR.exists() or not any(VECTOR_STORE_DIR.iterdir()):
            logger.info("No existing vector store to backup")
            return
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.backup_dir / f"backup_{timestamp}"
        
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            # Create a temporary directory for the backup
            temp_dir = self.backup_dir / f"temp_{timestamp}"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy everything except the backups directory
            for item in VECTOR_STORE_DIR.iterdir():
                if item.name != "backups":
                    if item.is_file():
                        shutil.copy2(item, temp_dir)
                    elif item.is_dir():
                        shutil.copytree(item, temp_dir / item.name)
            
            # Move the temporary directory to the final backup location
            shutil.move(str(temp_dir), str(backup_path))
            logger.info(f"Created backup at {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create backup: {str(e)}")
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
            raise

    def _clean_vector_store(self) -> None:
        """Clean the vector store directory."""
        try:
            if VECTOR_STORE_DIR.exists():
                self._create_backup()
                shutil.rmtree(VECTOR_STORE_DIR)
            VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
            logger.info("Vector store directory cleaned")
        except Exception as e:
            logger.error(f"Failed to clean vector store: {str(e)}")
            raise

    def _get_existing_sources(self) -> Set[str]:
        """Get list of sources from existing vector store."""
        if not self.metadata_file.exists():
            return set()
            
        try:
            with open(self.metadata_file, 'r') as f:
                metadata = json.load(f)
                return set(metadata.get('document_sources', []))
        except Exception as e:
            logger.error(f"Failed to read existing sources: {str(e)}")
            return set()

    def _get_modified_files(self, existing_sources: Set[str]) -> List[Path]:
        """Get list of modified files since last processing."""
        modified_files = []
        for source in existing_sources:
            file_path = Path(source)
            if file_path.exists():
                # Check if file was modified after last processing
                if self.metadata_file.exists():
                    last_modified = datetime.datetime.fromtimestamp(file_path.stat().st_mtime)
                    metadata_modified = datetime.datetime.fromtimestamp(self.metadata_file.stat().st_mtime)
                    if last_modified > metadata_modified:
                        modified_files.append(file_path)
        return modified_files

    def load_documents(self, incremental: bool = False) -> List[Document]:
        """Load documents from the data directory."""
        try:
            logger.info(f"Loading documents from {DATA_DIR}")
            
            if not DATA_DIR.exists():
                raise FileNotFoundError(f"Data directory not found: {DATA_DIR}")
            
            if incremental and self.metadata_file.exists():
                # Get existing sources and modified files
                existing_sources = self._get_existing_sources()
                modified_files = self._get_modified_files(existing_sources)
                
                # Load only new and modified files
                new_documents = []
                for file_path in modified_files:
                    try:
                        loader = TextLoader(str(file_path))
                        new_documents.extend(loader.load())
                    except Exception as e:
                        logger.warning(f"Failed to load {file_path}: {str(e)}")
                        continue
                
                if not new_documents:
                    logger.info("No new or modified documents found")
                    return []
                
                logger.info(f"Loaded {len(new_documents)} new/modified documents")
                return new_documents
            else:
                # Load all documents
                if not any(DATA_DIR.glob("**/*.md")):
                    raise FileNotFoundError(f"No markdown files found in {DATA_DIR}")
                
                loader = DirectoryLoader(
                    DATA_DIR,
                    glob="**/*.md",
                    loader_cls=TextLoader,
                    recursive=True
                )
                documents = loader.load()
                
                if not documents:
                    raise ValueError(f"No documents loaded from {DATA_DIR}")
                
                logger.info(f"Loaded {len(documents)} documents")
                return documents
                
        except Exception as e:
            logger.error(f"Failed to load documents: {str(e)}")
            raise

    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into smaller chunks for better embedding."""
        try:
            logger.info("Starting document splitting process")
            
            # First split by markdown headers
            markdown_splitter = MarkdownHeaderTextSplitter(
                headers_to_split_on=HEADERS_TO_SPLIT_ON
            )
            
            # Then split into smaller chunks if needed
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=CHUNK_SIZE,
                chunk_overlap=CHUNK_OVERLAP,
                length_function=len,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            
            all_chunks = []
            for doc in tqdm(documents, desc="Splitting documents"):
                try:
                    # First split by headers
                    header_splits = markdown_splitter.split_text(doc.page_content)
                    
                    # Then split each header section into smaller chunks if needed
                    for split in header_splits:
                        chunks = text_splitter.split_text(split.page_content)
                        for chunk in chunks:
                            # Create a new Document with combined metadata
                            new_doc = Document(
                                page_content=chunk,
                                metadata={
                                    **doc.metadata,  # Original document metadata
                                    **split.metadata,  # Header metadata
                                    "chunk_size": len(chunk)
                                }
                            )
                            all_chunks.append(new_doc)
                except Exception as e:
                    logger.warning(f"Failed to process document {doc.metadata.get('source', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Successfully created {len(all_chunks)} chunks from {len(documents)} documents")
            return all_chunks
        except Exception as e:
            logger.error(f"Failed to split documents: {str(e)}")
            raise

    def create_vector_store(self, documents: List[Document]) -> None:
        """Create and save FAISS vector store."""
        try:
            logger.info("Creating FAISS vector store...")
            self.vector_store = FAISS.from_documents(documents, self.embeddings)
            
            # Create vector store directory if it doesn't exist
            VECTOR_STORE_DIR.mkdir(parents=True, exist_ok=True)
            
            logger.info("Saving vector store...")
            self.vector_store.save_local(str(VECTOR_STORE_DIR))
            
            # Save metadata about the vector store
            self._save_metadata(documents)
            
            logger.info(f"Vector store saved to {VECTOR_STORE_DIR}")
        except Exception as e:
            logger.error(f"Failed to create vector store: {str(e)}")
            raise

    def _save_metadata(self, documents: List[Document]) -> None:
        """Save metadata about the vector store."""
        # Calculate statistics about chunks
        chunk_sizes = [len(doc.page_content) for doc in documents]
        avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
        
        # Group documents by type (role, skill, learning path)
        doc_types = {}
        for doc in documents:
            source = doc.metadata.get("source", "unknown")
            if "roles" in source:
                doc_types["roles"] = doc_types.get("roles", 0) + 1
            elif "skills" in source:
                doc_types["skills"] = doc_types.get("skills", 0) + 1
            elif "learning_paths" in source:
                doc_types["learning_paths"] = doc_types.get("learning_paths", 0) + 1
        
        metadata = {
            "total_documents": len(documents),
            "document_types": doc_types,
            "chunk_size": CHUNK_SIZE,
            "chunk_overlap": CHUNK_OVERLAP,
            "chunk_statistics": {
                "average_size": round(avg_chunk_size, 2),
                "min_size": min(chunk_sizes) if chunk_sizes else 0,
                "max_size": max(chunk_sizes) if chunk_sizes else 0,
                "total_chunks": len(chunk_sizes)
            },
            "embedding_model": EMBEDDING_MODEL,
            "document_sources": list(set(doc.metadata.get("source", "unknown") for doc in documents)),
            "creation_timestamp": datetime.datetime.now().isoformat(),
            "vector_store_path": str(VECTOR_STORE_DIR),
            "processing_parameters": {
                "headers_to_split_on": HEADERS_TO_SPLIT_ON,
                "separators": ["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            }
        }
        
        with open(VECTOR_STORE_DIR / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
            
        # Also save a human-readable summary
        with open(VECTOR_STORE_DIR / "metadata_summary.txt", "w") as f:
            f.write(f"Vector Store Summary\n")
            f.write(f"===================\n\n")
            f.write(f"Created: {metadata['creation_timestamp']}\n")
            f.write(f"Total Documents: {metadata['total_documents']}\n")
            f.write(f"\nDocument Types:\n")
            for doc_type, count in metadata['document_types'].items():
                f.write(f"- {doc_type}: {count}\n")
            f.write(f"\nChunk Statistics:\n")
            f.write(f"- Average Size: {metadata['chunk_statistics']['average_size']} characters\n")
            f.write(f"- Min Size: {metadata['chunk_statistics']['min_size']} characters\n")
            f.write(f"- Max Size: {metadata['chunk_statistics']['max_size']} characters\n")
            f.write(f"- Total Chunks: {metadata['chunk_statistics']['total_chunks']}\n")
            f.write(f"\nEmbedding Model: {metadata['embedding_model']}\n")
            f.write(f"\nDocument Sources:\n")
            for source in sorted(metadata['document_sources']):
                f.write(f"- {source}\n")

    def process_documents(self, incremental: bool = False):
        """Process documents and create/update vector store."""
        try:
            # Initialize embeddings
            self.initialize_embeddings()
            
            if not incremental:
                # Full reprocessing
                self._clean_vector_store()
            
            # Load documents
            documents = self.load_documents(incremental)
            
            if not documents:
                logger.info("No documents to process")
                return
            
            # Split documents
            chunks = self.split_documents(documents)
            
            if not chunks:
                logger.warning("No chunks created from documents")
                return
            
            if incremental and self.vector_store is not None:
                # Add new chunks to existing vector store
                self.vector_store.add_documents(chunks)
            else:
                # Create new vector store
                self.vector_store = FAISS.from_documents(chunks, self.embeddings)
            
            # Save vector store
            self.vector_store.save_local(str(VECTOR_STORE_DIR))
            
            # Update metadata
            self._save_metadata(documents)
            
            logger.info("Document processing completed successfully")
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            raise

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Process documents for vector store')
    parser.add_argument('--incremental', action='store_true',
                      help='Perform incremental update instead of full reprocessing')
    args = parser.parse_args()
    
    try:
        embedder = DocumentEmbedder()
        embedder.process_documents(incremental=args.incremental)
    except Exception as e:
        logger.error(f"Script execution failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 