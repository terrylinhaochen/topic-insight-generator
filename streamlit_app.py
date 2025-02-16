import streamlit as st
import json
import os
from datetime import datetime
from backend.utils.prompt_handler import PromptHandler

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
            
            # Call Claude API
            response = st.session_state.get('claude_client').post(
                'http://localhost:3001/api/generate',
                json=prompt_data
            )
            
            if response.status_code != 200:
                st.error("Failed to generate insight. Please try again.")
            else:
                data = response.json()
                
                # Parse the response
                try:
                    text = data['content'][0]['text'].strip()
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

# Add some spacing
st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center'>
    <p>Built with Streamlit • Powered by Claude</p>
</div>
""", unsafe_allow_html=True) 