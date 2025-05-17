import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.schema import Document
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
ROOT_DIR = Path(__file__).parent.parent
VECTOR_STORE_DIR = ROOT_DIR / "rag" / "vector_store"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

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
        self.embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
        self.vector_store = FAISS.load_local(
            str(VECTOR_STORE_DIR),
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        
        # Initialize Neo4j driver
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        
        # Cache for role and skill information
        self._role_cache = {}
        self._skill_cache = {}
        
        # Create QA prompt
        self.qa_prompt = self._create_qa_prompt()

    def _create_qa_prompt(self) -> PromptTemplate:
        """Create the QA prompt template."""
        template = """You are a career development assistant helping engineers navigate their career paths.
Use the following pieces of context to answer the question at the end.
The context includes both unstructured content and structured knowledge from our career graph.

Context from documents:
{document_context}

Context from knowledge graph:
{graph_context}

Question: {question}

Answer: Let me help you with that. """

        return PromptTemplate(
            template=template,
            input_variables=["document_context", "graph_context", "question"]
        )

    def answer_question(self, query: str) -> str:
        """Answer a question using both graph and vector store data."""
        try:
            # Get context from both sources
            graph_context = self.get_graph_context(query)
            relevant_docs = self._get_relevant_documents(query)
            
            # Format the answer based on the context
            answer = []
            
            # Add graph context if available
            if graph_context and graph_context != "No specific roles or skills mentioned in the query.":
                answer.append("Based on the career graph:")
                answer.append(graph_context)
            
            # Add relevant documents
            if relevant_docs:
                answer.append("\nAdditional Resources:")
                for i, doc in enumerate(relevant_docs, 1):
                    answer.append(f"\nResource {i}:")
                    answer.append(f"Source: {doc.metadata.get('source', 'unknown')}")
                    answer.append(f"Content: {doc.page_content[:200]}...")
            
            return "\n".join(answer) if answer else "I couldn't find specific information to answer your question. Please try rephrasing it or ask about specific roles or skills."
            
        except Exception as e:
            logger.error(f"Failed to answer question: {str(e)}")
            return "I encountered an error while processing your question. Please try again."

    def _load_vector_store(self) -> FAISS:
        """Load the FAISS vector store."""
        try:
            vector_store = FAISS.load_local(
                str(VECTOR_STORE_DIR),
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            logger.info("Vector store loaded successfully")
            return vector_store
        except Exception as e:
            logger.error(f"Failed to load vector store: {str(e)}")
            raise

    def _get_graph_context(self, query_type: str, **kwargs) -> str:
        """Get relevant context from the knowledge graph."""
        try:
            with self.driver.session(database=self.database) as session:
                if query_type == "role_skills":
                    return session.run("""
                        MATCH (r:Role {name: $role_name})-[:REQUIRES]->(s:Skill)
                        RETURN collect(s.name) as skills
                    """, role_name=kwargs['role']).single()["skills"]
                
                elif query_type == "transition_path":
                    return session.run("""
                        MATCH path = shortestPath((r1:Role {name: $from_role})-[*..5]->(r2:Role {name: $to_role}))
                        RETURN [node in nodes(path) | node.name] as path,
                               [rel in relationships(path) | type(rel)] as relationships
                    """, from_role=kwargs['from_role'], to_role=kwargs['to_role']).single()["path"]
                
                elif query_type == "skill_hierarchy":
                    return session.run("""
                        MATCH (s:Skill {name: $skill_name})-[:PREREQUISITE*]->(prereq:Skill)
                        RETURN collect(prereq.name) as prerequisites
                    """, skill_name=kwargs['skill']).single()["prerequisites"]
                
                return []
        except Exception as e:
            logger.error(f"Failed to get graph context: {str(e)}")
            return []

    def _get_relevant_documents(self, query: str, k: int = 3) -> List[Document]:
        """Retrieve relevant documents from the vector store."""
        try:
            docs = self.vector_store.similarity_search(query, k=k)
            return docs
        except Exception as e:
            logger.error(f"Failed to retrieve documents: {str(e)}")
            raise

    def _format_context(self, docs: List[Document]) -> str:
        """Format the retrieved documents into a context string."""
        context_parts = []
        for doc in docs:
            source = doc.metadata.get("source", "unknown")
            section = doc.metadata.get("Header 1", "")
            subsection = doc.metadata.get("Header 2", "")
            
            context_parts.append(f"From {source}")
            if section:
                context_parts.append(f"Section: {section}")
            if subsection:
                context_parts.append(f"Subsection: {subsection}")
            context_parts.append(doc.page_content)
            context_parts.append("---")
        
        return "\n".join(context_parts)

    def get_role_info(self, role: str) -> Dict:
        """Get detailed information about a role for the UI."""
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (r:Role {name: $role})
                OPTIONAL MATCH (r)-[:REQUIRES_SKILL]->(s:Skill)
                WITH r, collect(DISTINCT s.name) as skills
                OPTIONAL MATCH (r)-[:REQUIRES_LEVEL]->(l:Level)
                RETURN r.name as name, skills, collect(DISTINCT l.name) as levels
            """, role=role)
            record = result.single()
            if not record:
                return None
            return {
                'name': record['name'],
                'skills': record['skills'] if record['skills'] and record['skills'][0] is not None else [],
                'levels': record['levels'] if record['levels'] and record['levels'][0] is not None else []
            }
    
    def get_transition_path(self, from_role: str, to_role: str) -> str:
        """Get transition path information for the UI."""
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH path = shortestPath((r1:Role {name: $from_role})-[*..5]->(r2:Role {name: $to_role}))
                RETURN [node in nodes(path) | node.name] as path,
                       [rel in relationships(path) | type(rel)] as relationships
            """, from_role=from_role, to_role=to_role)
            
            record = result.single()
            if not record:
                return None
            
            path = record['path']
            relationships = record['relationships']
            
            # Get skill differences
            skill_diff = self._get_skill_differences(session, from_role, to_role)
            
            # Format the path information
            info = []
            info.append(f"From {from_role} to {to_role}:")
            
            if skill_diff:
                if skill_diff.get("Skills to Learn"):
                    info.append("\nSkills to Learn:")
                    info.extend([f"- {skill}" for skill in skill_diff["Skills to Learn"]])
                
                if skill_diff.get("Skills to Maintain"):
                    info.append("\nSkills to Maintain:")
                    info.extend([f"- {skill}" for skill in skill_diff["Skills to Maintain"]])
                
                if skill_diff.get("Skills to Phase Out"):
                    info.append("\nSkills to Phase Out:")
                    info.extend([f"- {skill}" for skill in skill_diff["Skills to Phase Out"]])
            
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
        
        skills1 = set(record['skills1']) if record['skills1'] and record['skills1'][0] is not None else set()
        skills2 = set(record['skills2']) if record['skills2'] and record['skills2'][0] is not None else set()
        
        return {
            "Skills to Learn": list(skills2 - skills1),
            "Skills to Maintain": list(skills1 & skills2),
            "Skills to Phase Out": list(skills1 - skills2)
        }
    
    def get_skill_info(self, skill: str) -> str:
        """Get detailed information about a skill for the UI."""
        with self.driver.session(database=self.database) as session:
            result = session.run("""
                MATCH (s:Skill {name: $skill})
                OPTIONAL MATCH (r:Role)-[:REQUIRES_SKILL]->(s)
                RETURN s.name as name,
                       collect(DISTINCT r.name) as required_by_roles
            """, skill=skill)
            record = result.single()
            if not record:
                return None
            info = f"Skill: {record['name']}\n"
            if record['required_by_roles'] and record['required_by_roles'][0] is not None:
                info += "Required by Roles: " + ", ".join(record['required_by_roles'])
            return info

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
                    role_info = self.get_role_info(role)
                    if role_info:
                        context.append(f"Role: {role_info['name']}")
                        if role_info['levels']:
                            context.append("Levels: " + ", ".join(role_info['levels']))
                        if role_info['skills']:
                            context.append("Skills: " + ", ".join(role_info['skills']))
            # Get skill information
            if skills:
                context.append("\nSkill Information:")
                for skill in skills:
                    skill_info = self.get_skill_info(skill)
                    if skill_info:
                        context.append(skill_info)
            # Get transition paths if multiple roles are mentioned
            if len(roles) >= 2:
                context.append("\nTransition Path:")
                transition_info = self.get_transition_path(roles[0], roles[1])
                if transition_info:
                    context.append(transition_info)
            return "\n".join(context) if context else "No specific roles or skills mentioned in the query."
    
    def _extract_roles(self, query: str) -> List[str]:
        """Extract role names from the query using improved matching."""
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
        skills = [
            "Python", "SQL", "Power BI", "Tableau", "Data Warehousing",
            "ETL Processes", "Statistics", "Machine Learning", "Deep Learning",
            "MLOps", "Cloud Platforms"
        ]
        query_lower = query.lower()
        return [skill for skill in skills if skill.lower() in query_lower]
    
    def get_skill_gaps(self, current_role: str, target_role: str) -> str:
        """Get skill gaps between current and target roles."""
        try:
            # Get required skills for both roles from graph
            current_skills = self._get_graph_context("role_skills", role=current_role)
            target_skills = self._get_graph_context("role_skills", role=target_role)
            
            # Find missing skills
            missing_skills = set(target_skills) - set(current_skills)
            
            # Get detailed information about missing skills
            question = f"What skills do I need to develop to transition from {current_role} to {target_role}? Specifically, I need to learn: {', '.join(missing_skills)}"
            return self.answer_question(question)
        except Exception as e:
            logger.error(f"Failed to get skill gaps: {str(e)}")
            raise

    def get_role_description(self, role: str) -> str:
        """Get detailed description of a role."""
        try:
            # Get required skills from graph
            required_skills = self._get_graph_context("role_skills", role=role)
            
            # Enhance the question with graph knowledge
            question = f"What are the key responsibilities and requirements for a {role}? The role requires these skills: {', '.join(required_skills)}"
            return self.answer_question(question)
        except Exception as e:
            logger.error(f"Failed to get role description: {str(e)}")
            raise

    def get_learning_path(self, from_role: str, to_role: str) -> str:
        """Get a learning path between two roles."""
        try:
            # Get transition path from graph
            path = self._get_graph_context("transition_path", from_role=from_role, to_role=to_role)
            
            # Get required skills for each role in the path
            skills_by_role = {}
            for role in path:
                skills_by_role[role] = self._get_graph_context("role_skills", role=role)
            
            # Enhance the question with graph knowledge
            question = f"What is the recommended learning path to transition from {from_role} to {to_role}? The path includes these roles: {', '.join(path)}"
            return self.answer_question(question)
        except Exception as e:
            logger.error(f"Failed to get learning path: {str(e)}")
            raise

    def __del__(self):
        """Clean up Neo4j connection."""
        if hasattr(self, 'driver'):
            self.driver.close() 