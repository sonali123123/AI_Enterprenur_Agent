from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class TextResponse(BaseModel):
    response: str
    suggestions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class VoiceResponse(BaseModel):
    audio_content: bytes
    text_response: str
    suggestions: List[str] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SuggestionResponse(BaseModel):
    suggestions: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
