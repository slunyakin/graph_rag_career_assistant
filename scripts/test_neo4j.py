import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_neo4j_connection():
    """Test Neo4j connection and basic queries."""
    # Load environment variables
    load_dotenv()
    
    # Get Neo4j credentials
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")
    
    if not password:
        raise ValueError("NEO4J_PASSWORD environment variable is required")
    
    try:
        # Create driver instance
        logger.info(f"Connecting to Neo4j at {uri} (database: {database})...")
        driver = GraphDatabase.driver(uri, auth=(user, password))
        
        # Test connection
        with driver.session(database=database) as session:
            # Test 1: Basic connection
            result = session.run("RETURN 1 as test")
            test_value = result.single()["test"]
            logger.info(f"Basic connection test: {'✓' if test_value == 1 else '✗'}")
            
            # Test 2: List all roles
            result = session.run("MATCH (r:Role) RETURN r.name as role")
            roles = [record["role"] for record in result]
            logger.info(f"\nFound {len(roles)} roles:")
            for role in roles:
                logger.info(f"- {role}")
            
            # Test 3: List all skills
            result = session.run("MATCH (s:Skill) RETURN s.name as skill")
            skills = [record["skill"] for record in result]
            logger.info(f"\nFound {len(skills)} skills:")
            for skill in skills:
                logger.info(f"- {skill}")
            
            # Test 4: Get role-skill relationships with more detailed query
            result = session.run("""
                MATCH (r:Role)
                OPTIONAL MATCH (r)-[rel]->(s:Skill)
                RETURN r.name as role, 
                       collect(DISTINCT {skill: s.name, type: type(rel)}) as relationships
                ORDER BY r.name
            """)
            logger.info("\nRole-Skill Relationships:")
            for record in result:
                role = record["role"]
                relationships = record["relationships"]
                if relationships and relationships[0]["skill"] is not None:
                    logger.info(f"\n{role}:")
                    for rel in relationships:
                        logger.info(f"  - {rel['type']} -> {rel['skill']}")
                else:
                    logger.info(f"\n{role}: No relationships found")
            
            # Test 5: Check for any relationships in the graph
            result = session.run("""
                MATCH ()-[r]->()
                RETURN DISTINCT type(r) as relationship_type, count(*) as count
            """)
            logger.info("\nRelationship Types in Graph:")
            for record in result:
                logger.info(f"- {record['relationship_type']}: {record['count']} relationships")
        
        logger.info("\nAll Neo4j tests completed!")
        return True
        
    except Exception as e:
        logger.error(f"Neo4j test failed: {str(e)}")
        return False
    finally:
        if 'driver' in locals():
            driver.close()

if __name__ == "__main__":
    test_neo4j_connection() 