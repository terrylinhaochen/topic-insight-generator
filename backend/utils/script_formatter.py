import re
import json

def parse_script_response(text):
    """
    Parse a non-JSON script response from Claude into a structured format.
    This is used as a fallback when the response isn't in proper JSON format.
    
    Args:
        text (str): The raw text response from Claude
        
    Returns:
        dict: A structured dictionary with script components
    """
    result = {
        "title": "",
        "description": "",
        "script": "",
        "primary_chapter": "",
        "supporting_chapters": []
    }
    
    # Try to extract title
    title_match = re.search(r"(?:Title:|Episode Title:)\s*(.*?)(?:\n|$)", text, re.IGNORECASE)
    if title_match:
        result["title"] = title_match.group(1).strip()
    
    # Try to extract description
    desc_match = re.search(r"(?:Description:|Episode Description:)\s*(.*?)(?:\n\n|\n(?:Script:|Books:|Chapters:|Primary))", text, re.IGNORECASE | re.DOTALL)
    if desc_match:
        result["description"] = desc_match.group(1).strip()
    
    # Try to extract script content - check various patterns
    script_match = re.search(r"(?:Script:|Podcast Script:)\s*(.*?)(?:\n\n(?:References:|Books:|Chapters:|Primary)|$)", text, re.DOTALL | re.IGNORECASE)
    if script_match:
        result["script"] = script_match.group(1).strip()
    else:
        # Try to find script between description and books/references
        desc_end_pos = text.find(result["description"]) + len(result["description"]) if result["description"] else 0
        if desc_end_pos > 0:
            # Find the next section after description
            next_section_match = re.search(r"\n\n(Books:|Chapters:|References:|Primary)", text[desc_end_pos:], re.IGNORECASE)
            if next_section_match:
                next_section_pos = desc_end_pos + next_section_match.start()
                # Extract anything between description and next section as the script
                potential_script = text[desc_end_pos:next_section_pos].strip()
                if potential_script and not potential_script.startswith(("Books:", "Chapters:", "References:", "Primary")):
                    result["script"] = potential_script
    
    # First try to find a "Books:" or "Chapters:" section
    books_section = re.search(r"(?:Books:|Chapters:|References:)\s*(.*?)(?:\n\n|$)", text, re.DOTALL | re.IGNORECASE)
    
    if books_section:
        books_text = books_section.group(1).strip()
        
        # Try to extract primary book/chapter
        primary_match = re.search(r"(?:Primary:?|Primary Chapter:?|Primary Reference:?)\s*(.*?)(?:Supporting:?|$)", books_text, re.DOTALL | re.IGNORECASE)
        if primary_match:
            primary_text = primary_match.group(1).strip()
            
            # Try to match JSON format
            try:
                # Clean up the text to make it more JSON-like
                primary_text = primary_text.replace("'", '"')
                # Add quotes to keys if missing
                primary_text = re.sub(r'(\s*)(\w+)(\s*:)', r'\1"\2"\3', primary_text)
                
                # Try to parse as JSON
                if '{' in primary_text and '}' in primary_text:
                    json_text = primary_text[primary_text.find('{'):primary_text.rfind('}')+1]
                    primary_json = json.loads(json_text)
                    
                    # Get title from either 'title', 'chapter', or just use the whole primary_text
                    title = primary_json.get('title') or primary_json.get('chapter')
                    author = primary_json.get('author', 'Sun Tzu')
                    
                    if title:
                        result["primary_chapter"] = f"{title} by {author}"
                    else:
                        result["primary_chapter"] = primary_text
                else:
                    result["primary_chapter"] = primary_text
            except Exception:
                # If JSON parsing fails, just use the text
                result["primary_chapter"] = primary_text
        
        # Try to extract supporting books/chapters
        supporting_match = re.search(r"(?:Supporting:?|Supporting Chapters:?|Supporting References:?)\s*(.*?)(?:$)", books_text, re.DOTALL | re.IGNORECASE)
        if supporting_match:
            supporting_text = supporting_match.group(1).strip()
            
            # Try different approaches to extract supporting items
            
            # First, try to find JSON-like objects
            json_objects = re.findall(r'{[^{}]*}', supporting_text)
            if json_objects:
                for obj_text in json_objects:
                    try:
                        # Make it more JSON-like
                        clean_obj = obj_text.replace("'", '"')
                        # Add quotes to keys if missing
                        clean_obj = re.sub(r'(\s*)(\w+)(\s*:)', r'\1"\2"\3', clean_obj)
                        
                        obj = json.loads(clean_obj)
                        title = obj.get('title') or obj.get('chapter')
                        author = obj.get('author', 'Sun Tzu')
                        
                        if title:
                            result["supporting_chapters"].append(f"{title} by {author}")
                    except Exception:
                        # If JSON parsing fails, just use the text
                        result["supporting_chapters"].append(obj_text.strip())
            else:
                # If no JSON objects found, try to extract bullet points
                chapters = re.findall(r"[-•*\d+\.]\s*(.*?)(?:\n|$)", supporting_text)
                if chapters:
                    result["supporting_chapters"] = [ch.strip() for ch in chapters if ch.strip()]
                else:
                    # Last resort, split by newlines
                    chapters = [line.strip() for line in supporting_text.split('\n') if line.strip()]
                    result["supporting_chapters"] = chapters
    else:
        # Try to extract primary chapter directly
        primary_match = re.search(r"(?:Primary Chapter:|Primary Reference:)\s*(.*?)(?:\n|$)", text, re.IGNORECASE)
        if primary_match:
            result["primary_chapter"] = primary_match.group(1).strip()
        
        # Try to extract supporting chapters directly
        supporting_section = re.search(r"(?:Supporting Chapters:|Supporting References:)\s*(.*?)(?:$)", text, re.DOTALL | re.IGNORECASE)
        if supporting_section:
            supporting_text = supporting_section.group(1).strip()
            # Extract individual items that start with a dash, bullet, number or asterisk
            chapters = re.findall(r"[-•*\d+\.]\s*(.*?)(?:\n|$)", supporting_text)
            result["supporting_chapters"] = [ch.strip() for ch in chapters if ch.strip()]
    
    return result 