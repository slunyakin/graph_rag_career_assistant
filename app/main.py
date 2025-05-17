import os
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv
from rag.pipeline import CareerRAG

# Configure page
st.set_page_config(
    page_title="AskCareer: Your Engineering Path Coach",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load environment variables
load_dotenv()

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stTextInput>div>div>input {
        font-size: 1.2rem;
    }
    .stButton>button {
        width: 100%;
        font-size: 1.2rem;
        padding: 0.5rem 1rem;
    }
    .role-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .skill-list {
        margin: 0.5rem 0;
    }
    .transition-path {
        background-color: #e6f3ff;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

def initialize_rag():
    """Initialize the RAG pipeline."""
    if 'rag' not in st.session_state:
        with st.spinner('Initializing career assistant...'):
            st.session_state.rag = CareerRAG()

def display_role_info(role_info):
    """Display role information in a formatted card."""
    st.markdown(f"""
        <div class="role-card">
            <h3>{role_info['name']}</h3>
            <p><strong>Levels:</strong> {', '.join(role_info['levels'])}</p>
            <div class="skill-list">
                <strong>Required Skills:</strong>
                <ul>
                    {''.join(f'<li>{skill}</li>' for skill in role_info['skills'])}
                </ul>
            </div>
        </div>
    """, unsafe_allow_html=True)

def display_transition_path(path_info):
    """Display transition path information."""
    st.markdown(f"""
        <div class="transition-path">
            <h3>Transition Path</h3>
            {path_info}
        </div>
    """, unsafe_allow_html=True)

def display_answer(answer):
    """Display the answer with formatted paragraphs and lists."""
    st.markdown("### Answer")
    # Split the answer into paragraphs and format each
    paragraphs = answer.split('\n\n')
    for paragraph in paragraphs:
        if paragraph.startswith("Based on the career graph:"):
            st.markdown(paragraph)
        else:
            st.markdown(paragraph)

def display_resources(resources):
    """Display resources as a separate section with clickable links."""
    st.markdown("### Additional Resources")
    for resource in resources:
        st.markdown(f"- [{resource.metadata.get('title', 'Resource')}]({resource.metadata.get('source', '#')})")

def main():
    # Initialize RAG pipeline
    initialize_rag()
    
    # Header
    st.title("🚀 AskCareer: Your Engineering Path Coach")
    st.markdown("""
        Get personalized guidance for your engineering career path. 
        Ask questions about roles, skills, and transitions.
    """)
    
    # Sidebar
    with st.sidebar:
        st.header("Quick Actions")
        st.markdown("""
            ### Example Questions:
            - What skills do I need for a Data Engineer role?
            - How can I transition from BI Engineer to Data Engineer?
            - What's the difference between Data Analyst and Data Engineer?
            - What skills should I focus on for Machine Learning?
        """)
        
        st.header("About")
        st.markdown("""
            AskCareer uses Role Ontology Graphs and RAG to provide 
            personalized career guidance for engineers.
        """)
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Question input
        question = st.text_input(
            "Ask your career question:",
            placeholder="e.g., What skills do I need to become a Data Engineer?"
        )
        
        if question:
            with st.spinner('Analyzing your question...'):
                # Get answer from RAG pipeline
                answer = st.session_state.rag.answer_question(question)
                
                # Display answer
                display_answer(answer)
                
                # Display resources
                resources = st.session_state.rag._get_relevant_documents(question)
                display_resources(resources)
    
    with col2:
        # Role exploration
        st.header("Explore Roles")
        role = st.selectbox(
            "Select a role to explore:",
            ["Data Engineer", "BI Engineer", "Data Analyst", "Machine Learning Engineer"]
        )
        
        if role:
            with st.spinner('Loading role information...'):
                # Get role information
                role_info = st.session_state.rag.get_role_info(role)
                if role_info:
                    display_role_info(role_info)
                
                # Get transition paths
                st.header("Possible Transitions")
                for target_role in ["Data Engineer", "BI Engineer", "Data Analyst", "Machine Learning Engineer"]:
                    if target_role != role:
                        path_info = st.session_state.rag.get_transition_path(role, target_role)
                        if path_info:
                            display_transition_path(path_info)

if __name__ == "__main__":
    main() 