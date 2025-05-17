import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.llms import HuggingFaceHub
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CareerRAG:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Initialize Neo4j connection
        self.uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = os.getenv("NEO4J_USER", "neo4j")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")
        
        if not self.password:
            raise ValueError("NEO4J_PASSWORD environment variable is required")
        
        # Initialize vector store
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.vector_store = FAISS.load_local(
            str(Path("rag/vector_store")),
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        # Cache for role and skill information
        self._role_cache = {}
        self._skill_cache = {}
    
    def get_graph_context(self, query: str) -> str:
        """Get relevant context from the graph database."""
        with self.driver.session(database=self.database) as session:
            # Extract roles and skills from the query
            roles = self._extract_roles(query)
            skills = self._extract_skills(query)
            
            context = []
            
            # Get role information
            if roles:
                context.append("Role Information:")
                for role in roles:
                    role_info = self._get_role_info(session, role)
                    if role_info:
                        context.append(role_info)
            
            # Get skill information
            if skills:
                context.append("\nSkill Information:")
                for skill in skills:
                    skill_info = self._get_skill_info(session, skill)
                    if skill_info:
                        context.append(skill_info)
            
            # Get transition paths if multiple roles are mentioned
            if len(roles) >= 2:
                context.append("\nTransition Path:")
                transition_info = self._get_transition_path(session, roles[0], roles[1])
                if transition_info:
                    context.append(transition_info)
            
            return "\n".join(context) if context else "No specific roles or skills mentioned in the query."
    
    def _get_role_info(self, session, role: str) -> str:
        """Get detailed information about a role."""
        if role in self._role_cache:
            return self._role_cache[role]
        
        result = session.run("""
            MATCH (r:Role {name: $role})
            OPTIONAL MATCH (r)-[rel]->(s:Skill)
            OPTIONAL MATCH (r)-[:REQUIRES_LEVEL]->(l)
            RETURN r.name as role,
                   collect(DISTINCT {skill: s.name, type: type(rel)}) as skills,
                   collect(DISTINCT l.name) as levels
        """, role=role)
        
        record = result.single()
        if not record:
            return f"Role '{role}' not found in the database."
        
        info = [f"\nRole: {record['role']}"]
        
        # Add levels
        levels = record['levels']
        if levels and levels[0] is not None:
            info.append("Career Levels:")
            for level in levels:
                info.append(f"- {level}")
        
        # Add skills
        skills = record['skills']
        if skills and skills[0]['skill'] is not None:
            info.append("\nRequired Skills:")
            for skill in skills:
                info.append(f"- {skill['skill']}")
        
        # Cache the result
        self._role_cache[role] = "\n".join(info)
        return self._role_cache[role]
    
    def _get_skill_info(self, session, skill: str) -> str:
        """Get detailed information about a skill."""
        if skill in self._skill_cache:
            return self._skill_cache[skill]
        
        result = session.run("""
            MATCH (s:Skill {name: $skill})
            OPTIONAL MATCH (r:Role)-[rel]->(s)
            RETURN s.name as skill,
                   collect(DISTINCT {role: r.name, type: type(rel)}) as roles
        """, skill=skill)
        
        record = result.single()
        if not record:
            return f"Skill '{skill}' not found in the database."
        
        info = [f"\nSkill: {record['skill']}"]
        
        # Add roles that require this skill
        roles = record['roles']
        if roles and roles[0]['role'] is not None:
            info.append("\nRequired by Roles:")
            for role in roles:
                info.append(f"- {role['role']}")
        
        # Cache the result
        self._skill_cache[skill] = "\n".join(info)
        return self._skill_cache[skill]
    
    def _get_transition_path(self, session, from_role: str, to_role: str) -> str:
        """Get detailed transition path between roles."""
        result = session.run("""
            MATCH path = shortestPath((r1:Role {name: $from_role})-[*..5]->(r2:Role {name: $to_role}))
            RETURN [node in nodes(path) | node.name] as path,
                   [rel in relationships(path) | type(rel)] as relationships
        """, from_role=from_role, to_role=to_role)
        
        record = result.single()
        if not record:
            return f"No direct transition path found from {from_role} to {to_role}."
        
        path = record['path']
        relationships = record['relationships']
        
        info = [f"\nTransition from {from_role} to {to_role}:"]
        
        # Add path steps
        for i in range(len(path) - 1):
            current_role = path[i]
            next_role = path[i + 1]
            rel_type = relationships[i]
            info.append(f"\nStep {i + 1}: {current_role} -> {next_role}")
            info.append(f"Relationship: {rel_type}")
            
            # Get skill differences
            skill_diff = self._get_skill_differences(session, current_role, next_role)
            if skill_diff:
                info.append("Skill Changes:")
                for skill_type, skills in skill_diff.items():
                    if skills:
                        info.append(f"- {skill_type}: {', '.join(skills)}")
        
        return "\n".join(info)
    
    def _get_skill_differences(self, session, role1: str, role2: str) -> Dict[str, List[str]]:
        """Get skill differences between two roles."""
        result = session.run("""
            MATCH (r1:Role {name: $role1})-[:REQUIRES_SKILL]->(s1:Skill)
            MATCH (r2:Role {name: $role2})-[:REQUIRES_SKILL]->(s2:Skill)
            RETURN collect(DISTINCT s1.name) as skills1,
                   collect(DISTINCT s2.name) as skills2
        """, role1=role1, role2=role2)
        
        record = result.single()
        if not record:
            return {}
        
        skills1 = set(record['skills1'])
        skills2 = set(record['skills2'])
        
        return {
            "Skills to Learn": list(skills2 - skills1),
            "Skills to Maintain": list(skills1 & skills2),
            "Skills to Phase Out": list(skills1 - skills2)
        }
    
    def _extract_roles(self, query: str) -> List[str]:
        """Extract role names from the query using improved matching."""
        # This is a simple implementation. In a real system, you might want to use NLP
        roles = ["BI Engineer", "Data Engineer", "Data Analyst", "Machine Learning Engineer"]
        query_lower = query.lower()
        
        # Check for exact matches first
        exact_matches = [role for role in roles if role.lower() in query_lower]
        if exact_matches:
            return exact_matches
        
        # Check for partial matches
        partial_matches = []
        for role in roles:
            # Split role into words and check if all words are present
            role_words = role.lower().split()
            if all(word in query_lower for word in role_words):
                partial_matches.append(role)
        
        return partial_matches
    
    def _extract_skills(self, query: str) -> List[str]:
        """Extract skill names from the query."""
        # This is a simple implementation. In a real system, you might want to use NLP
        skills = [
            "Python", "SQL", "Power BI", "Tableau", "Data Warehousing",
            "ETL Processes", "Statistics", "Machine Learning", "Deep Learning",
            "MLOps", "Cloud Platforms"
        ]
        query_lower = query.lower()
        return [skill for skill in skills if skill.lower() in query_lower]
    
    def get_relevant_documents(self, query: str, k: int = 3) -> list:
        """Get relevant documents from the vector store."""
        return self.vector_store.similarity_search(query, k=k)
    
    def answer_question(self, query: str) -> str:
        """Answer a question using both graph and vector store data."""
        # Get context from both sources
        graph_context = self.get_graph_context(query)
        relevant_docs = self.get_relevant_documents(query)
        
        # Combine the information
        answer = f"Based on the career graph and available resources:\n\n"
        
        # Add graph context
        answer += graph_context + "\n\n"
        
        # Add relevant documents
        answer += "Additional Resources:\n"
        for i, doc in enumerate(relevant_docs, 1):
            answer += f"\nResource {i}:\n"
            answer += f"Source: {doc.metadata.get('source', 'unknown')}\n"
            answer += f"Content: {doc.page_content[:200]}...\n"
        
        return answer

def main():
    """Test the RAG pipeline with sample questions."""
    try:
        rag = CareerRAG()
        
        # Test questions
        questions = [
            "What skills do I need to become a Data Engineer?",
            "How can I transition from BI Engineer to Data Engineer?",
            "What are the key differences between Data Analyst and Data Engineer roles?",
            "What skills should I focus on to move from Data Analyst to Machine Learning Engineer?",
            "Tell me about the Python skills needed for data roles"
        ]
        
        for question in questions:
            logger.info(f"\nQuestion: {question}")
            answer = rag.answer_question(question)
            logger.info(f"\nAnswer:\n{answer}")
            logger.info("-" * 80)
            
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        raise
    finally:
        if 'rag' in locals():
            rag.driver.close()

if __name__ == "__main__":
    main() 