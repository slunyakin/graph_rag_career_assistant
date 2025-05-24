from setuptools import setup, find_packages

setup(
    name="graph_rag_career_assistant",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "langchain-huggingface>=0.0.5",
        "sentence-transformers>=2.2.2",
        "faiss-cpu>=1.7.4",
        "neo4j>=5.0.0",
        "python-dotenv>=1.0.0",
        "streamlit>=1.30.0",
        "huggingface-hub>=0.20.0"
    ],
) 