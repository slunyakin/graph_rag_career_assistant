import os
from pathlib import Path
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ROOT_DIR = Path(__file__).parent.parent
VECTOR_STORE_DIR = ROOT_DIR / "rag" / "vector_store"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def load_vector_store():
    """Load the FAISS vector store."""
    try:
        embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        vector_store = FAISS.load_local(
            str(VECTOR_STORE_DIR), 
            embeddings,
            allow_dangerous_deserialization=True  # Safe since we created the vector store
        )
        logger.info("Vector store loaded successfully")
        return vector_store
    except Exception as e:
        logger.error(f"Failed to load vector store: {str(e)}")
        raise

def test_queries(vector_store):
    """Test the vector store with sample queries."""
    test_queries = [
        "What are the key responsibilities of a Data Engineer?",
        "What skills are needed for Machine Learning?",
        "How to transition from BI Engineer to Data Engineer?",
        "What is the role of SQL in data analysis?",
        "What are the main differences between Data Analyst and ML Engineer?"
    ]
    
    for query in test_queries:
        logger.info(f"\nQuery: {query}")
        docs = vector_store.similarity_search(query, k=2)
        for i, doc in enumerate(docs, 1):
            logger.info(f"\nResult {i}:")
            logger.info(f"Source: {doc.metadata.get('source', 'unknown')}")
            logger.info(f"Content: {doc.page_content[:200]}...")  # Show first 200 chars
            if 'Header 1' in doc.metadata:
                logger.info(f"Section: {doc.metadata['Header 1']}")
            if 'Header 2' in doc.metadata:
                logger.info(f"Subsection: {doc.metadata['Header 2']}")

def main():
    """Main function to test embeddings."""
    try:
        vector_store = load_vector_store()
        test_queries(vector_store)
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 