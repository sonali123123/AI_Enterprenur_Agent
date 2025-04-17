import json
import logging
from typing import List, Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def format_conversation_for_context(
    messages: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """
    Format conversation history for the AI model context.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        
    Returns:
        Formatted list of messages for the AI model
    """
    formatted_messages = []
    
    for message in messages:
        if 'role' in message and 'content' in message:
            formatted_messages.append({
                'role': message['role'],
                'content': message['content']
            })
    
    return formatted_messages

def parse_json_string(json_string: str) -> Optional[Any]:
    """
    Safely parse a JSON string.
    
    Args:
        json_string: JSON string to parse
        
    Returns:
        Parsed JSON object or None if parsing fails
    """
    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing JSON: {str(e)}")
        return None

def extract_json_from_text(text: str) -> Optional[Any]:
    """
    Extract JSON from text that might contain other content.
    
    Args:
        text: Text that might contain JSON
        
    Returns:
        Extracted JSON object or None if extraction fails
    """
    try:
        # Try to find JSON object in the text
        import re
        json_match = re.search(r'(\{|\[).*(\}|\])', text, re.DOTALL)
        
        if json_match:
            json_str = json_match.group(0)
            return json.loads(json_str)
        
        return None
    
    except Exception as e:
        logger.error(f"Error extracting JSON from text: {str(e)}")
        return None

def truncate_text(text: str, max_length: int = 100) -> str:
    """
    Truncate text to a maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length of the truncated text
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length] + "..."
