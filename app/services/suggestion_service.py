import random
from typing import List, Optional
import logging

from app.config import ENTREPRENEURSHIP_TOPICS, MAX_SUGGESTIONS
from app.services.ai_service import ai_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SuggestionService:
    def __init__(self):
        self.topics = ENTREPRENEURSHIP_TOPICS
        self.max_suggestions = MAX_SUGGESTIONS
    
    def get_default_suggestions(self) -> List[str]:
        """Get default suggestions when no context is available."""
        # Randomly select topics for suggestions
        selected_topics = random.sample(self.topics, min(self.max_suggestions, len(self.topics)))
        
        # Create suggestions based on the selected topics
        suggestions = []
        for topic in selected_topics:
            suggestion_type = random.choice([
                "Tell me about",
                "How do I approach",
                "What are best practices for",
                "What are common mistakes in",
                "How can I improve my",
                "What tools can help with"
            ])
            suggestions.append(f"{suggestion_type} {topic}?")
        
        return suggestions
    
    def get_contextual_suggestions(self, message: str, response: str) -> List[str]:
        """Get contextual suggestions based on the conversation."""
        try:
            # Use the AI service to generate contextual suggestions
            suggestions = ai_service.generate_suggestions(message, response)
            
            # Ensure we have the right number of suggestions
            if len(suggestions) > self.max_suggestions:
                suggestions = suggestions[:self.max_suggestions]
            elif len(suggestions) < self.max_suggestions:
                # Add some default suggestions if we don't have enough
                additional = self.get_default_suggestions()
                suggestions.extend(additional[:(self.max_suggestions - len(suggestions))])
            
            return suggestions
        
        except Exception as e:
            logger.error(f"Error generating contextual suggestions: {str(e)}")
            return self.get_default_suggestions()

# Create a singleton instance
suggestion_service = SuggestionService()
