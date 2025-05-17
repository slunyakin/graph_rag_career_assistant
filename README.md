# AskCareer: Your Engineering Path Coach

An AI-powered career assistant that helps engineers navigate their career paths using Role Ontology Graphs and Retrieval-Augmented Generation (RAG).

## Features

- Career path exploration and transition planning
- Skill gap analysis and learning recommendations
- Role-based insights and requirements
- Integration of structured graph data with unstructured content
- Natural language Q&A interface

## Prerequisites

### Python Environment
- Python 3.8 or higher
- Virtual environment (recommended)

### Neo4j Database
- Neo4j Desktop or Neo4j Community Edition
- Database name (default: "neo4j")
- Username and password
- Bolt connection URI (default: "bolt://localhost:7687")

### Environment Variables
Create a `.env` file in the project root with the following variables:
```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_DATABASE=your_database_name
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/askcareer.git
cd askcareer
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Neo4j Database Setup
1. Start Neo4j Desktop and create a new database
2. Ensure the database is running and accessible with the credentials specified in your `.env` file
3. Populate the graph database with initial data:
```bash
# Initialize the graph database with roles, skills, and relationships
cypher-shell -u neo4j -p your_password -f graph/cypher/init_graph.cypher
```

### Document Processing
Process documents for the vector store:
```bash
# Full reprocessing
python scripts/embed_documents.py

# Incremental update
python scripts/embed_documents.py --incremental
```

### Running the Application
Start the Streamlit interface:
```bash
streamlit run app/main.py
```

## Testing

### Vector Store Testing
Test the document embedding and vector store:
```bash
PYTHONPATH=. python scripts/test_embeddings.py
```

### Neo4j Connection Testing
Test the Neo4j database connection and graph queries:
```bash
PYTHONPATH=. python scripts/test_neo4j.py
```

### RAG Pipeline Testing
Test the complete RAG pipeline with sample questions:
```bash
PYTHONPATH=. python scripts/test_rag_pipeline.py
```

## Project Structure

```
askcareer/
├── app/                  → Streamlit UI components
├── config/              → Configuration files
├── data/                → Role and skill content
├── docs/                → Documentation
├── graph/               → Neo4j graph scripts
├── rag/                 → RAG pipeline components
│   ├── documents/       → Processed documents
│   └── vector_store/    → FAISS indexes
└── scripts/             → Utility scripts
```

> Note: Detailed documentation for specific components can be found in their respective directories (e.g., `scripts/EMBEDDING.md` for document embedding details).

## Testing Scripts

### test_embeddings.py
- Tests document loading and chunking
- Validates vector store creation
- Checks embedding quality

### test_neo4j.py
- Verifies Neo4j connection
- Tests graph queries
- Validates role and skill relationships

### test_rag_pipeline.py
- Tests the complete RAG pipeline
- Validates role and skill extraction
- Checks transition path generation
- Tests document retrieval

## Development

### Adding New Content
1. Add role/skill documents to `data/`
2. Process documents: `python scripts/embed_documents.py`
3. Test embeddings: `python scripts/test_embeddings.py`

### Updating Graph Data
1. Modify Cypher scripts in `graph/cypher/`
2. Test graph: `python scripts/test_neo4j.py`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

The GPL v3 ensures that:
- All derivatives of this project must also be open source
- Commercial use is allowed, but the code must remain open
- The project and its derivatives must be distributed under the same license

## Acknowledgments

- Neo4j for graph database
- FAISS for vector similarity search
- LangChain for RAG pipeline
- HuggingFace for embeddings