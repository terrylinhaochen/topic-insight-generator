import streamlit as st
import json
import os
import sys
from datetime import datetime
import re

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
        
        # Initialize with simpler API pattern
        st.session_state.claude_client = Anthropic(
            api_key=api_key,
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

# Function to find the most relevant chapter using Claude
def find_relevant_chapters(user_input, chapter_summaries, num_chapters=2):
    if not chapter_summaries:
        return []
    
    # Create a prompt for Claude to select the most relevant chapter
    system_prompt = """You are a literary analysis assistant. Your task is to analyze a given topic and select the most relevant chapters from "The Art of War" that connect to this topic. Consider themes, principles, and lessons that could be applied metaphorically or directly. Return your answer as a JSON array containing the chapter titles in order of relevance."""
    
    chapters_text = "\n\n".join([f"Chapter {ch['CHAPTER_NUMBER']}: {ch['TITLE']} - {ch['SUMMARY']}" for ch in chapter_summaries])
    
    user_prompt = f"""Topic: {user_input}

Available chapters from "The Art of War":
{chapters_text}

Return the {num_chapters} most relevant chapters for this topic as a JSON array of chapter titles.
Example: ["Chapter II: Waging War", "Chapter V: Energy"]"""

    try:
        # Call Claude to get the most relevant chapters
        response = st.session_state.claude_client.messages.create(
            model="claude-3-7-sonnet-20250219",
            max_tokens=300,
            temperature=0.2,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract the JSON array from the response
        text = response.content[0].text.strip()
        start_idx = text.find('[')
        end_idx = text.rfind(']') + 1
        
        if start_idx >= 0 and end_idx > start_idx:
            json_str = text[start_idx:end_idx]
            relevant_chapters = json.loads(json_str)
            return relevant_chapters[:num_chapters]  # Return the top chapters
        else:
            # Return the first two chapters if parsing fails
            return [f"Chapter {chapter_summaries[0]['CHAPTER_NUMBER']}: {chapter_summaries[0]['TITLE']}",
                    f"Chapter {chapter_summaries[1]['CHAPTER_NUMBER']}: {chapter_summaries[1]['TITLE']}"]
    except Exception as e:
        st.error(f"Error finding relevant chapters: {str(e)}")
        # Return the first two chapters as fallback
        return [f"Chapter {chapter_summaries[0]['CHAPTER_NUMBER']}: {chapter_summaries[0]['TITLE']}",
                f"Chapter {chapter_summaries[1]['CHAPTER_NUMBER']}: {chapter_summaries[1]['TITLE']}"]

# Function to get chapter summary by title
def get_chapter_by_title(chapter_title, chapter_summaries):
    for chapter in chapter_summaries:
        if f"Chapter {chapter['CHAPTER_NUMBER']}: {chapter['TITLE']}" == chapter_title:
            return chapter
    return None

# Function to fetch chapter quotes
def fetch_chapter_quotes(chapter_title, chapter_summaries):
    # Extract chapter number and name
    if "Chapter" not in chapter_title or ":" not in chapter_title:
        return "No quotes available for this chapter."
    
    chapter = get_chapter_by_title(chapter_title, chapter_summaries)
    if not chapter:
        return "Chapter not found in summaries."
    
    chapter_number = chapter['CHAPTER_NUMBER']
    
    # Map roman numerals to digits if needed
    roman_to_digit = {
        "I": "01", "II": "02", "III": "03", "IV": "04", "V": "05",
        "VI": "06", "VII": "07", "VIII": "08", "IX": "09", "X": "10",
        "XI": "11", "XII": "12", "XIII": "13"
    }
    
    file_number = roman_to_digit.get(chapter_number, chapter_number)
    chapter_name = chapter['TITLE']
    
    # Try to find and read the file
    try:
        # Format possible filenames
        possible_paths = [
            f"backend/config/books/the_art_of_war/quotes/{file_number}_{chapter_name.replace(' ', '_')}.md",
            f"backend/config/books/the_art_of_war/quotes/{file_number.zfill(2)}_{chapter_name.replace(' ', '_')}.md"
        ]
        
        for file_path in possible_paths:
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Try to extract quotes
                quotes = []
                verse_pattern = re.compile(r'"VERSE":\s*"(\d+)".*?"TEXT":\s*"([^"]+)"', re.DOTALL)
                matches = verse_pattern.findall(content)
                
                if matches:
                    for verse, text in matches:
                        quotes.append(f"Verse {verse}: {text}")
                    return "\n\n".join(quotes[:5])  # Return first 5 quotes
                
                return "No quotes could be extracted from the chapter file."
        
        return "Chapter file not found."
    except Exception as e:
        return f"Error fetching quotes: {str(e)}"

# Page config
st.set_page_config(
    page_title="For every question, a book awaits",
    page_icon="🎙️",
    layout="centered"
)

# Title and description
st.title("For every question, a book awaits")
st.markdown("""
Generate insightful podcast scripts that connect everyday topics to wisdom from Sun Tzu's "The Art of War".
""")

# Load chapter summaries
try:
    chapter_summaries_path = os.path.join('backend', 'config', 'books', 'the_art_of_war', 'processed', 'chapter_summaries.json')
    
    if os.path.exists(chapter_summaries_path):
        with open(chapter_summaries_path, 'r') as f:
            data = json.load(f)
            chapter_summaries = data.get('CHAPTER_SUMMARIES', [])
        
        if chapter_summaries:
            st.success(f"Loaded {len(chapter_summaries)} chapters from The Art of War")
        else:
            st.warning("No chapters found in the summaries file")
            chapter_summaries = []
    else:
        st.warning(f"Chapter summaries file not found at: {chapter_summaries_path}")
        chapter_summaries = []
except Exception as e:
    st.warning(f"Error loading chapter summaries: {str(e)}")
    chapter_summaries = []

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

# RAG mode toggle
rag_mode = st.checkbox("Use AI to automatically find relevant chapters", value=True)

# Debug mode toggle
debug_mode = st.checkbox("Enable Debug Mode", value=False)

# Manual JSON input in debug mode
if debug_mode:
    st.info("Debug Mode Enabled - You can test the JSON parsing directly")
    manual_json = st.text_area(
        "Test JSON Input (optional)",
        placeholder='Paste a JSON response to test parsing...',
        height=200
    )
    
    if manual_json and st.button("Parse JSON"):
        try:
            # Try to parse the JSON
            result = json.loads(manual_json)
            
            # Display the raw JSON structure
            with st.expander("Debug: View Raw JSON Response"):
                st.json(result)
            
            # Transform/fix the JSON structure if needed
            transformed_result = result.copy()
            
            # Check for and fix missing fields
            if 'episodeTitle' not in transformed_result:
                st.warning("Missing 'episodeTitle' field - adding a default title")
                transformed_result['episodeTitle'] = "Insights from The Art of War"
            
            if 'description' not in transformed_result:
                st.warning("Missing 'description' field - adding a default description")
                transformed_result['description'] = "Connecting modern challenges to ancient wisdom from Sun Tzu"
            
            # Convert 'books' to 'chapters' if needed (common issue)
            if 'books' in transformed_result and 'chapters' not in transformed_result:
                st.warning("Found 'books' field instead of 'chapters' - converting to proper format")
                transformed_result['chapters'] = transformed_result['books']
                del transformed_result['books']
            
            # Fix chapters structure if it's not in the expected format
            if 'chapters' in transformed_result:
                # If chapters is a list/array instead of an object with primary/supporting
                if isinstance(transformed_result['chapters'], list):
                    st.warning("The 'chapters' field is an array instead of the expected object structure - restructuring it")
                    chapters_list = transformed_result['chapters']
                    
                    # Create the correct structure
                    transformed_result['chapters'] = {
                        'primary': {
                            'chapter': chapters_list[0]['title'] if len(chapters_list) > 0 and 'title' in chapters_list[0] else "Chapter from The Art of War",
                            'author': 'Sun Tzu'
                        },
                        'supporting': []
                    }
                    
                    # Add any additional chapters as supporting
                    if len(chapters_list) > 1:
                        for chapter in chapters_list[1:]:
                            transformed_result['chapters']['supporting'].append({
                                'title': chapter.get('title', "Chapter from The Art of War"),
                                'author': 'Sun Tzu'
                            })
            else:
                st.warning("Missing 'chapters' field - adding a default structure")
                transformed_result['chapters'] = {
                    'primary': {
                        'chapter': "The Art of War",
                        'author': 'Sun Tzu'
                    },
                    'supporting': []
                }
            
            # Display the transformed JSON structure
            with st.expander("Debug: View Transformed JSON"):
                st.json(transformed_result)
            
            # Display the podcast script
            st.subheader("Generated Podcast Script")
            
            # Episode title with styling
            st.markdown(f"### {transformed_result['episodeTitle']}")
            
            # Description
            st.markdown(f"_{transformed_result['description']}_")
            
            # Script content
            st.markdown("#### Script")
            st.markdown(transformed_result['script'])
            
            # References section
            st.subheader(f"References")
            
            # Primary reference
            if 'primary' in transformed_result['chapters']:
                primary = transformed_result['chapters']['primary']
                st.markdown(f"**Primary Chapter:**")
                
                # Get chapter title - try both 'chapter' and 'title' fields
                primary_title = primary.get('chapter') or primary.get('title') or "Untitled"
                primary_author = primary.get('author', 'Sun Tzu')
                st.markdown(f"- {primary_title} by {primary_author}")
            
            # Supporting references
            if 'supporting' in transformed_result['chapters'] and transformed_result['chapters']['supporting']:
                st.markdown(f"**Supporting Chapters:**")
                for item in transformed_result['chapters']['supporting']:
                    title = item.get('title') or item.get('chapter') or "Untitled"
                    author = item.get('author', 'Sun Tzu')
                    st.markdown(f"- {title} by {author}")
            
        except Exception as e:
            st.error(f"Error parsing the JSON: {str(e)}")
            st.code(manual_json)

# Chapter selection - only show if not using RAG
selected_chapters = []
if not rag_mode and chapter_summaries:
    st.subheader("Select chapters from 'The Art of War' to incorporate")
    chapter_options = [f"Chapter {ch['CHAPTER_NUMBER']}: {ch['TITLE']}" for ch in chapter_summaries]
    selected_chapters = st.multiselect(
        "Choose relevant chapters",
        options=chapter_options,
        default=[],
        help="Select one or more chapters to incorporate into your podcast script"
    )
    
    # Show summaries of selected chapters
    if selected_chapters:
        with st.expander("View selected chapter summaries"):
            for chapter_title in selected_chapters:
                chapter = get_chapter_by_title(chapter_title, chapter_summaries)
                if chapter:
                    st.markdown(f"**{chapter_title}**")
                    st.markdown(chapter['SUMMARY'])
                    st.markdown("---")

# Generate button
if st.button("Generate Podcast Script", disabled=not user_input):
    with st.spinner("Analyzing topic and finding relevant chapters..."):
        try:
            # Find relevant chapters if in RAG mode
            if rag_mode:
                selected_chapters = find_relevant_chapters(user_input, chapter_summaries)
                
                # Show the relevant chapters that were selected
                if selected_chapters:
                    st.info(f"AI selected the following relevant chapters: {', '.join(selected_chapters)}")
                    
                    with st.expander("View selected chapter summaries"):
                        for chapter_title in selected_chapters:
                            chapter = get_chapter_by_title(chapter_title, chapter_summaries)
                            if chapter:
                                st.markdown(f"**{chapter_title}**")
                                st.markdown(chapter['SUMMARY'])
                                st.markdown("---")

            # Format the prompt with selected chapters
            prompt_data = prompt_handler.format_prompt(domain, user_input)
            
            # Debug: Display the system prompt
            if debug_mode:
                with st.expander("Debug: View System Prompt Content"):
                    st.code(prompt_data['system'])
            
            # Get quotes from selected chapters
            chapters_with_quotes = []
            for chapter_title in selected_chapters:
                chapter = get_chapter_by_title(chapter_title, chapter_summaries)
                if chapter:
                    quotes = fetch_chapter_quotes(chapter_title, chapter_summaries)
                    chapters_with_quotes.append({
                        "title": chapter_title,
                        "summary": chapter['SUMMARY'],
                        "quotes": quotes
                    })
            
            # Add selected chapter content if available
            if chapters_with_quotes:
                chapters_content = "\n\n".join([
                    f"Chapter: {ch['title']}\nSummary: {ch['summary']}\nQuotes:\n{ch['quotes']}"
                    for ch in chapters_with_quotes
                ])
                enhanced_input = f"Topic: {user_input}\n\nRelevant Art of War Chapters with Quotes:\n{chapters_content}"
            else:
                enhanced_input = f"Topic: {user_input}"
            
            # Format the prompt according to Claude's requirements
            # Simply use the system prompt directly with the user's input (from career_single.py or parenting_single.py)
            formatted_prompt = f"{prompt_data['system']}\n\nHuman: {enhanced_input}\n\nAssistant:"
            
        except Exception as e:
            st.error(f"Error in preparation step: {str(e)}")
            st.stop()
        
    with st.spinner("Generating podcast script..."):
        try:
            # Call Claude API directly using the messages endpoint for Claude 3.7 Sonnet
            response = st.session_state.claude_client.messages.create(
                model="claude-3-7-sonnet-20250219",
                max_tokens=2000,
                temperature=0.7,
                system=prompt_data['system'],
                messages=[
                    {"role": "user", "content": enhanced_input}
                ]
            )
            
            # Parse the response from the messages API
            try:
                text = response.content[0].text.strip()
                
                # Store the raw response for debugging
                st.session_state.last_raw_response = text
                
                # First attempt: Try to find JSON in the response
                json_pattern = re.compile(r'({.*})', re.DOTALL)
                json_match = json_pattern.search(text)
                
                if json_match:
                    # Handle JSON format response
                    json_text = json_match.group(1)
                    result = json.loads(json_text)
                    
                    # Debug: Display the raw JSON structure
                    with st.expander("Debug: View Raw JSON Response"):
                        st.json(result)
                    
                    # Transform/fix the JSON structure if needed
                    transformed_result = result.copy()
                    
                    # Check for and fix missing fields
                    if 'episodeTitle' not in transformed_result:
                        st.warning("Missing 'episodeTitle' field - adding a default title")
                        transformed_result['episodeTitle'] = "Insights from The Art of War"
                    
                    if 'description' not in transformed_result:
                        st.warning("Missing 'description' field - adding a default description")
                        transformed_result['description'] = "Connecting modern challenges to ancient wisdom from Sun Tzu"
                    
                    # Convert 'books' to 'chapters' if needed (common issue)
                    if 'books' in transformed_result and 'chapters' not in transformed_result:
                        st.warning("Found 'books' field instead of 'chapters' - converting to proper format")
                        transformed_result['chapters'] = transformed_result['books']
                        del transformed_result['books']
                    
                    # Fix chapters structure if it's not in the expected format
                    if 'chapters' in transformed_result:
                        # If chapters is a list/array instead of an object with primary/supporting
                        if isinstance(transformed_result['chapters'], list):
                            st.warning("The 'chapters' field is an array instead of the expected object structure - restructuring it")
                            chapters_list = transformed_result['chapters']
                            
                            # Create the correct structure
                            transformed_result['chapters'] = {
                                'primary': {
                                    'chapter': chapters_list[0]['title'] if len(chapters_list) > 0 and 'title' in chapters_list[0] else "Chapter from The Art of War",
                                    'author': 'Sun Tzu'
                                },
                                'supporting': []
                            }
                            
                            # Add any additional chapters as supporting
                            if len(chapters_list) > 1:
                                for chapter in chapters_list[1:]:
                                    transformed_result['chapters']['supporting'].append({
                                        'title': chapter.get('title', "Chapter from The Art of War"),
                                        'author': 'Sun Tzu'
                                    })
                    else:
                        st.warning("Missing 'chapters' field - adding a default structure")
                        transformed_result['chapters'] = {
                            'primary': {
                                'chapter': "The Art of War",
                                'author': 'Sun Tzu'
                            },
                            'supporting': []
                        }
                    
                    # Display the transformed JSON structure
                    with st.expander("Debug: View Transformed JSON"):
                        st.json(transformed_result)
                    
                    # Continue with the transformed result
                    result = transformed_result
                    
                    # Validate the required fields
                    required_fields = ['episodeTitle', 'description', 'script', 'chapters']
                    missing_fields = [field for field in required_fields if field not in result]
                    
                    if missing_fields:
                        st.error(f"The response is missing the following required fields: {', '.join(missing_fields)}")
                        st.code(text)
                        st.stop()
                    
                    # Display the podcast script
                    st.subheader("Generated Podcast Script")
                    
                    # Episode title with styling
                    st.markdown(f"### {result['episodeTitle']}")
                    
                    # Description
                    st.markdown(f"_{result['description']}_")
                    
                    # Script content
                    st.markdown("#### Script")
                    st.markdown(result['script'])
                    
                    # Enhanced debugging for chapters structure
                    with st.expander("Debug: Raw Chapters Data"):
                        st.write("Raw chapters structure:")
                        st.json(result.get('chapters', {}))
                        
                        st.write("Expected structure:")
                        st.code("""{
  "primary": {
    "chapter": "The primary Art of War chapter used",
    "author": "Sun Tzu"
  },
  "supporting": [
    {
      "title": "First supporting chapter name",
      "author": "Sun Tzu"
    }
  ]
}""")
                    
                    # References section
                    st.subheader(f"References")
                    
                    # Validate chapters structure
                    if not isinstance(result['chapters'], dict):
                        st.error("The 'chapters' field is not a valid object")
                        st.json(result['chapters'])
                        st.stop()
                    
                    # Primary reference
                    if 'primary' in result['chapters']:
                        primary = result['chapters']['primary']
                        st.markdown(f"**Primary Chapter:**")
                        
                        # Get chapter title - try both 'chapter' and 'title' fields
                        primary_title = primary.get('chapter') or primary.get('title') or "Untitled"
                        primary_author = primary.get('author', 'Sun Tzu')
                        st.markdown(f"- {primary_title} by {primary_author}")
                        
                        # Debug primary chapter structure
                        with st.expander("Debug: Primary Chapter Structure"):
                            st.json(primary)
                    else:
                        st.warning("No primary reference found")
                        st.write("The 'primary' field is missing from the 'chapters' object.")
                    
                    # Supporting references
                    if 'supporting' in result['chapters'] and result['chapters']['supporting']:
                        st.markdown(f"**Supporting Chapters:**")
                        for item in result['chapters']['supporting']:
                            title = item.get('title') or item.get('chapter') or "Untitled"
                            author = item.get('author', 'Sun Tzu')
                            st.markdown(f"- {title} by {author}")
                        
                        # Debug supporting chapters structure
                        with st.expander("Debug: Supporting Chapters Structure"):
                            st.json(result['chapters']['supporting'])
                    else:
                        st.warning("No supporting references found")
                        if 'supporting' not in result['chapters']:
                            st.write("The 'supporting' field is missing from the 'chapters' object.")
                        elif not result['chapters']['supporting']:
                            st.write("The 'supporting' field is empty (no items in the array).")
                else:
                    # Handle plain text format
                    # Use our script_formatter to parse the response
                    try:
                        from utils.script_formatter import parse_script_response
                    except ImportError:
                        # If the module is not found, try to import from backend.utils
                        try:
                            from backend.utils.script_formatter import parse_script_response
                        except ImportError:
                            st.error("Could not import script_formatter - displaying raw text")
                            st.markdown("#### Script")
                            st.markdown(text)
                            st.stop()
                    
                    result = parse_script_response(text)
                    
                    # Debug: Display the parsed response
                    with st.expander("Debug: View Parsed Response"):
                        st.json(result)
                    
                    # Display the podcast script
                    st.subheader("Generated Podcast Script")
                    
                    # Title with styling
                    if result["title"]:
                        st.markdown(f"### {result['title']}")
                    
                    # Description
                    if result["description"]:
                        st.markdown(f"_{result['description']}_")
                    
                    # Script content
                    if result["script"]:
                        st.markdown("#### Script")
                        st.markdown(result['script'])
                    else:
                        # If no script section found, display the full text
                        st.markdown("#### Script")
                        st.markdown(text)
                    
                    # References section
                    st.subheader(f"References")
                    
                    # Primary reference
                    if result["primary_chapter"]:
                        st.markdown(f"**Primary Chapter:**")
                        st.markdown(f"- {result['primary_chapter']}")
                    
                    # Supporting references
                    if result["supporting_chapters"]:
                        st.markdown(f"**Supporting Chapters:**")
                        for chapter in result["supporting_chapters"]:
                            st.markdown(f"- {chapter}")
                    
            except Exception as e:
                st.error(f"Error parsing the response: {str(e)}")
                st.code(text)  # Show the raw text for debugging
                
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Full error details:")
            st.code(str(e))

    # Add a button to show the raw response text for debugging
    if debug_mode:
        if 'last_raw_response' in st.session_state:
            with st.expander("Debug: View Raw Claude Response"):
                st.text(st.session_state.last_raw_response)
    
# Add some spacing
st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center'>
    <p>Prototyping in Progress</p>
</div>
""", unsafe_allow_html=True) 