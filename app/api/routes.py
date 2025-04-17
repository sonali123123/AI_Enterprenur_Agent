from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import json
import logging
from typing import Optional, List, Dict, Any

from app.database import get_db, User, Conversation
from app.models.request_models import TextRequest, SuggestionRequest
from app.models.response_models import TextResponse, VoiceResponse, SuggestionResponse, ErrorResponse
from app.services.ai_service import ai_service
from app.services.voice_service import voice_service
from app.services.suggestion_service import suggestion_service

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Helper function to get or create user
def get_or_create_user(db: Session, user_id: str) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        user = User(id=user_id, username=f"user_{user_id[:8]}")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

# Helper function to save conversation
def save_conversation(
    db: Session, 
    user_id: str, 
    user_message: str, 
    bot_response: str, 
    suggestions: List[str]
) -> Conversation:
    # Get or create user
    user = get_or_create_user(db, user_id)
    
    # Create conversation record
    conversation = Conversation(
        user_id=user_id,
        user_message=user_message,
        bot_response=bot_response,
        suggestions=suggestions
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    return conversation

@router.post("/text", response_model=TextResponse)
async def process_text(
    request: TextRequest,
    db: Session = Depends(get_db)
):
    """
    Process text input and return AI response with suggestions.
    """
    try:
        # Generate response from AI service
        result = ai_service.generate_response(request.message, request.context)
        response_text = result["response"]
        
        # Generate suggestions
        suggestions = suggestion_service.get_contextual_suggestions(request.message, response_text)
        
        # Save conversation to database
        save_conversation(db, request.user_id, request.message, response_text, suggestions)
        
        return TextResponse(
            response=response_text,
            suggestions=suggestions
        )
    
    except Exception as e:
        logger.error(f"Error processing text request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice", response_model=VoiceResponse)
async def process_voice(
    audio_file: UploadFile = File(...),
    user_id: str = Form(...),
    context: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Process voice input and return AI voice response with suggestions.
    """
    try:
        # Read audio file
        audio_data = await audio_file.read()
        
        # Convert speech to text
        success, text = voice_service.speech_to_text(audio_data)
        
        if not success:
            return VoiceResponse(
                audio_content=voice_service.text_to_speech(text),
                text_response=text,
                suggestions=suggestion_service.get_default_suggestions()
            )
        
        # Parse context if provided
        context_data = []
        if context:
            try:
                context_data = json.loads(context)
            except json.JSONDecodeError:
                logger.warning("Failed to parse context JSON")
        
        # Generate response from AI service
        result = ai_service.generate_response(text, context_data)
        response_text = result["response"]
        
        # Generate suggestions
        suggestions = suggestion_service.get_contextual_suggestions(text, response_text)
        
        # Convert response to speech
        audio_content = voice_service.text_to_speech(response_text)
        
        # Save conversation to database
        save_conversation(db, user_id, text, response_text, suggestions)
        
        return VoiceResponse(
            audio_content=audio_content,
            text_response=response_text,
            suggestions=suggestions
        )
    
    except Exception as e:
        logger.error(f"Error processing voice request: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggestions", response_model=SuggestionResponse)
async def get_suggestions(
    request: SuggestionRequest,
    db: Session = Depends(get_db)
):
    """
    Get follow-up suggestions based on the conversation context.
    """
    try:
        # If message is provided, generate contextual suggestions
        if request.message:
            # Get the last bot response from context
            last_response = ""
            for item in reversed(request.context):
                if item.get("role") == "assistant":
                    last_response = item.get("content", "")
                    break
            
            suggestions = suggestion_service.get_contextual_suggestions(request.message, last_response)
        else:
            # Get default suggestions
            suggestions = suggestion_service.get_default_suggestions()
        
        return SuggestionResponse(suggestions=suggestions)
    
    except Exception as e:
        logger.error(f"Error getting suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audio/{text}")
async def get_audio(text: str):
    """
    Convert text to speech and return audio stream.
    """
    try:
        audio_content = voice_service.text_to_speech(text)
        return StreamingResponse(
            io.BytesIO(audio_content),
            media_type="audio/mpeg"
        )
    
    except Exception as e:
        logger.error(f"Error generating audio: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
