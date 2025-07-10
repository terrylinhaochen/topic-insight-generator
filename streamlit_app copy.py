import streamlit as st
import json
import os
import sys
from datetime import datetime

# Try to import dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    # Load environment variables from root directory
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass  # Running on Streamlit Cloud, will use st.secrets instead

# Add the backend directory to the Python path
backend_path = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.append(backend_path)

from utils.prompt_handler import PromptHandler
from anthropic import Anthropic
import httpx

# Initialize the Claude client
if 'claude_client' not in st.session_state:
    try:
        # Try to get API key from environment first, then from streamlit secrets
        api_key = os.getenv('CLAUDE_API_KEY') or st.secrets.get("CLAUDE_API_KEY")
        
        if not api_key:
            st.error("""
            CLAUDE_API_KEY not found. 
            
            If running locally:
            1. Create a .env file in the root directory
            2. Add the line: CLAUDE_API_KEY=your_api_key_here
            
            If running on Streamlit Cloud:
            1. Go to your app settings
            2. Add to .streamlit/secrets.toml:
               CLAUDE_API_KEY = "your_api_key_here"
            """)
            st.stop()
        
        # Initialize with timeout settings
        timeout = httpx.Timeout(30.0, connect=10.0)
        http_client = httpx.Client(timeout=timeout)
        st.session_state.claude_client = Anthropic(
            api_key=api_key,
            http_client=http_client
        )
    except Exception as e:
        st.error(f"Failed to initialize Claude client: {str(e)}")
        st.stop()

# Get Mastodon configuration
mastodon_config = {
    'access_token': os.getenv('MASTODON_ACCESS_TOKEN') or st.secrets.get("mastodon", {}).get("access_token"),
    'instance': os.getenv('MASTODON_INSTANCE') or st.secrets.get("mastodon", {}).get("instance")
}

# Initialize the PromptHandler
prompt_handler = PromptHandler()

# Page config
st.set_page_config(
    page_title="AI Insight Generator",
    page_icon="🎯",
    layout="centered"
)

# Title and description
st.title("AI Insight Generator")
st.markdown("""
Generate insightful podcast scripts for career development and parenting topics.
Connect everyday experiences to deeper patterns and unexpected domains using "The Art of War" principles.
""")

# Load chapter summaries
try:
    with open('chapter_summaries.json', 'r') as f:
        chapter_summaries = json.load(f)
    st.session_state['chapter_summaries'] = chapter_summaries
except Exception as e:
    st.warning("Chapter summaries not found. Some features may be limited.")
    chapter_summaries = {}
    st.session_state['chapter_summaries'] = {}

# Domain selection
domain = st.selectbox(
    "Choose Domain",
    ["career", "parenting"],
    format_func=lambda x: "Career Development" if x == "career" else "Parenting"
)

# Topic input area
user_input = st.text_area(
    "Share your topic",
    placeholder="Describe a workplace challenge or parenting situation..."
)

# Chapter selection
if chapter_summaries:
    st.subheader("Select chapters from 'The Art of War' to incorporate")
    selected_chapters = st.multiselect(
        "Choose relevant chapters",
        options=list(chapter_summaries.keys()),
        default=[],
        help="Select one or more chapters to incorporate into your podcast script"
    )
    
    # Show summaries of selected chapters
    if selected_chapters:
        with st.expander("View selected chapter summaries"):
            for chapter in selected_chapters:
                st.markdown(f"**{chapter}**")
                st.markdown(chapter_summaries[chapter])
                st.markdown("---")

# Generate button
if st.button("Generate Podcast Script", disabled=not user_input):
    with st.spinner("Generating script..."):
        try:
            # Format the prompt with selected chapters
            prompt_data = prompt_handler.format_prompt(domain, user_input)
            
            # Add selected chapter content if available
            if selected_chapters:
                chapters_content = "\n\n".join([
                    f"Chapter: {chapter}\nSummary: {chapter_summaries[chapter]}"
                    for chapter in selected_chapters
                ])
                enhanced_input = f"Topic: {user_input}\n\nRelevant Art of War Chapters:\n{chapters_content}"
            else:
                enhanced_input = f"Topic: {user_input}"
            
            # Format the prompt according to Claude's requirements
            formatted_prompt = f"{prompt_data['system']}\n\nHuman: Generate a podcast script about: {enhanced_input}\n\nAssistant:"
            
            # Call Claude API directly using the completions endpoint
            response = st.session_state.claude_client.completions.create(
                model="claude-2.1",
                prompt=formatted_prompt,
                max_tokens_to_sample=2000,
                temperature=0.7
            )
            
            # Parse the response
            try:
                text = response.completion.strip()
                json_match = text[text.find('{'):text.rfind('}')+1]
                result = json.loads(json_match)
                
                # Display the podcast script
                st.subheader("Generated Podcast Script")
                
                # Episode title with styling
                st.markdown(f"### {result['episodeTitle']}")
                
                # Description
                st.markdown(f"_{result['description']}_")
                
                # Script
                st.markdown("#### Script")
                st.markdown(result['script'])
                
                # Chapters used
                st.subheader("Chapters Referenced")
                
                # Primary chapter
                st.markdown("**Primary Chapter:**")
                st.markdown(f"- {result['chapters']['primary']['chapter']} by {result['chapters']['primary']['author']}")
                
                # Supporting chapters
                st.markdown("**Supporting Chapters:**")
                for chapter in result['chapters']['supporting']:
                    st.markdown(f"- {chapter['title']} by {chapter['author']}")
                
            except Exception as e:
                st.error(f"Error parsing the response: {str(e)}")
                st.code(text)  # Show the raw text for debugging
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Full error details:")
            st.code(str(e))

# Add some spacing
st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center'>
    <p>Built with Streamlit • Powered by Claude • Inspired by Sun Tzu's "The Art of War"</p>
</div>
""", unsafe_allow_html=True) 