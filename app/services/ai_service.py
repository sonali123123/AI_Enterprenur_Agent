import requests
import json
from typing import List, Dict, Any, Optional
import logging

from app.config import OLLAMA_API_URL, MODEL_NAME, MAX_CONVERSATION_HISTORY, ENTREPRENEURSHIP_TOPICS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_url = OLLAMA_API_URL
        self.model_name = MODEL_NAME
        self.max_history = MAX_CONVERSATION_HISTORY
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for the AI model."""
        return """
        You are an AI Entrepreneur Mentor Chatbot named Dr. Kartik, a seasoned startup expert with a PhD in Business Administration.
        Your role is to provide mentorship and guidance to aspiring entrepreneurs.
        
        Guidelines:
        1. Provide specific, actionable advice related to entrepreneurship, not generic responses.
        2. Focus on practical steps and real-world examples.
        3. Maintain a professional but encouraging tone.
        4. When discussing topics, provide depth rather than breadth.
        5. Cite relevant business concepts, methodologies, or frameworks when appropriate.
        6. Avoid political opinions or controversial statements.
        7. If asked about non-entrepreneurship topics, politely redirect to business-related discussions.
        
        Your expertise includes: business model development, startup funding, market research, product development,
        customer acquisition, scaling strategies, pitch deck creation, financial planning, team building,
        competitive analysis, and other entrepreneurship-related topics.
        """
    
    def _prepare_conversation_context(self, context: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Prepare the conversation context for the AI model."""
        # Limit the context to the maximum history size
        if len(context) > self.max_history:
            context = context[-self.max_history:]
        
        # Format the context for the model
        formatted_context = []
        for message in context:
            if message.get("role") and message.get("content"):
                formatted_context.append({
                    "role": message["role"],
                    "content": message["content"]
                })
        
        # Add system prompt at the beginning if not present
        if not formatted_context or formatted_context[0].get("role") != "system":
            formatted_context.insert(0, {
                "role": "system",
                "content": self.system_prompt
            })
        
        return formatted_context
    
    def generate_response(self, message: str, context: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Generate a response from the AI model."""
        if context is None:
            context = []
        
        # Prepare the conversation context
        conversation = self._prepare_conversation_context(context)
        
        # Add the current message
        conversation.append({
            "role": "user",
            "content": message
        })
        
        try:
            # Make the API request to Ollama
            payload = {
                "model": self.model_name,
                "messages": conversation,
                "stream": False
            }
            
            logger.info(f"Sending request to Ollama API: {json.dumps(payload)}")
            
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Received response from Ollama API: {result}")
            
            # Extract the response text
            response_text = result.get("message", {}).get("content", "")
            if not response_text:
                response_text = "I apologize, but I couldn't generate a response at this time. Please try again."
            
            return {
                "response": response_text,
                "context": conversation + [{"role": "assistant", "content": response_text}]
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            return {
                "response": "I'm having trouble connecting to my knowledge base. Please try again later.",
                "context": conversation
            }
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return {
                "response": "An unexpected error occurred. Please try again.",
                "context": conversation
            }
    
    def generate_suggestions(self, message: str, response: str) -> List[str]:
        """Generate follow-up suggestions based on the conversation."""
        # Create a prompt to generate suggestions
        suggestion_prompt = f"""
        Based on the following conversation between a user and an AI entrepreneur mentor,
        generate 4 specific follow-up questions that the user might want to ask next.
        
        User: {message}
        
        AI Mentor: {response}
        
        The follow-up questions should:
        1. Be directly related to entrepreneurship
        2. Follow naturally from the conversation
        3. Encourage deeper exploration of the topic
        4. Be specific and actionable
        
        Format the response as a JSON array of strings, with each string being a question.
        """
        
        try:
            # Make the API request to Ollama
            payload = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that generates follow-up questions."},
                    {"role": "user", "content": suggestion_prompt}
                ],
                "stream": False
            }
            
            response = requests.post(self.api_url, json=payload)
            response.raise_for_status()
            
            result = response.json()
            suggestion_text = result.get("message", {}).get("content", "")
            
            # Try to parse the JSON response
            try:
                # Find JSON array in the response
                import re
                json_match = re.search(r'\[.*\]', suggestion_text, re.DOTALL)
                if json_match:
                    suggestions = json.loads(json_match.group(0))
                    # Ensure we have the right number of suggestions
                    if len(suggestions) > 4:
                        suggestions = suggestions[:4]
                    return suggestions
            except json.JSONDecodeError:
                pass
            
            # Fallback: Generate default suggestions based on topics
            import random
            return [
                f"Can you tell me more about {random.choice(ENTREPRENEURSHIP_TOPICS)}?",
                f"What are the best practices for {random.choice(ENTREPRENEURSHIP_TOPICS)}?",
                f"How do I develop a strategy for {random.choice(ENTREPRENEURSHIP_TOPICS)}?",
                f"What common mistakes should I avoid in {random.choice(ENTREPRENEURSHIP_TOPICS)}?"
            ]
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {str(e)}")
            # Fallback to default suggestions
            return [
                "Can you tell me more about creating a business plan?",
                "What are the most important aspects of market research?",
                "How do I approach potential investors?",
                "What are the key metrics I should track for my startup?"
            ]

# Create a singleton instance
ai_service = AIService()
