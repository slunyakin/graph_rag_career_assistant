import os
from pathlib import Path
import logging
from rag.pipeline import CareerRAG
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    """Test the RAG pipeline with sample questions."""
    try:
        # Get Neo4j connection details from environment
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_password = os.getenv("NEO4J_PASSWORD")
        
        if not neo4j_password:
            raise ValueError("NEO4J_PASSWORD environment variable is required")
        
        # Initialize RAG pipeline
        rag = CareerRAG()
        
        # Test questions
        test_cases = [
            {
                "type": "role_description",
                "role": "Data Engineer",
                "question": "What are the key responsibilities of a Data Engineer?"
            },
            {
                "type": "skill_gaps",
                "from_role": "BI Engineer",
                "to_role": "Data Engineer",
                "question": "What skills do I need to develop to transition from BI Engineer to Data Engineer?"
            },
            {
                "type": "learning_path",
                "from_role": "Data Analyst",
                "to_role": "Machine Learning Engineer",
                "question": "What is the recommended learning path to transition from Data Analyst to ML Engineer?"
            }
        ]
        
        # Run tests
        for case in test_cases:
            logger.info(f"\nTesting {case['type']}:")
            logger.info(f"Question: {case['question']}")
            
            if case['type'] == 'role_description':
                response = rag.get_role_description(case['role'])
            elif case['type'] == 'skill_gaps':
                response = rag.get_skill_gaps(case['from_role'], case['to_role'])
            else:  # learning_path
                response = rag.get_learning_path(case['from_role'], case['to_role'])
            
            logger.info(f"Response: {response}")
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise

if __name__ == "__main__":
    main() 