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
Generate insightful discussion topics and book recommendations for career development and parenting.
Connect everyday experiences to deeper patterns and unexpected domains.
""")

# Domain selection
domain = st.selectbox(
    "Choose Domain",
    ["career", "parenting"],
    format_func=lambda x: "Career Development" if x == "career" else "Parenting"
)

# Input text area
user_input = st.text_area(
    "Share your challenge or topic",
    placeholder="Describe your situation or challenge..."
)

# Generate button
if st.button("Generate Insight", disabled=not user_input):
    with st.spinner("Generating insight..."):
        try:
            # Format the prompt
            prompt_data = prompt_handler.format_prompt(domain, user_input)
            
            # Format the prompt according to Claude's requirements
            formatted_prompt = f"{prompt_data['system']}\n\nHuman: Generate a podcast episode about: {prompt_data['user']}\n\nAssistant:"
            
            # Call Claude API directly using the completions endpoint
            response = st.session_state.claude_client.completions.create(
                model="claude-2.1",
                prompt=formatted_prompt,
                max_tokens_to_sample=1500,
                temperature=0.7
            )
            
            # Parse the response
            try:
                text = response.completion.strip()
                json_match = text[text.find('{'):text.rfind('}')+1]
                insight = json.loads(json_match)
                
                # Display the insight
                st.subheader("Generated Insight")
                
                # Episode title with styling
                st.markdown(f"### {insight['episodeTitle']}")
                
                # Description
                st.markdown(f"_{insight['description']}_")
                
                # Book recommendations
                st.subheader("📚 Recommended Reading")
                
                # Primary book
                st.markdown("**Core Book:**")
                st.markdown(f"- {insight['books']['primary']['title']} by {insight['books']['primary']['author']}")
                
                # Supporting books
                st.markdown("**Supporting Books:**")
                for book in insight['books']['supporting']:
                    st.markdown(f"- {book['title']} by {book['author']}")
                
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
    <p>Built with Streamlit • Powered by Claude</p>
</div>
""", unsafe_allow_html=True) 