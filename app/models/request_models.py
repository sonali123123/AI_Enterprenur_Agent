from pydantic import BaseModel, Field
from typing import Optional, List
import uuid

class TextRequest(BaseModel):
    user_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    message: str = Field(..., min_length=1)
    context: Optional[List[dict]] = Field(default_factory=list)

class VoiceRequest(BaseModel):
    user_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))
    # The actual voice data will be handled via form data
    context: Optional[List[dict]] = Field(default_factory=list)

class SuggestionRequest(BaseModel):
    user_id: str
    message: Optional[str] = None
    context: Optional[List[dict]] = Field(default_factory=list)
