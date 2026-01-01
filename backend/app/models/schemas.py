from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

class MessageSchema(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime

class UserProfileSchema(BaseModel):
    name: Optional[str] = None
    dob: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None

class ServiceSchema(BaseModel):
    id: str
    name: str
    duration_minutes: int
    price_eur: float
    description: str
    what_is_included: str
    how_its_done: str
    special_preparation: Optional[str] = None

class BookingSchema(BaseModel):
    id: Optional[str] = None
    service_id: str
    user_name: str
    user_dob: str
    user_phone: Optional[str] = None
    date: str
    time: str
    status: str = "confirmed"
    created_at: Optional[datetime] = None

class ConversationStateSchema(BaseModel):
    session_id: str
    messages: List[MessageSchema] = []
    user_profile: UserProfileSchema = UserProfileSchema()
    current_intent: Optional[str] = None
    extracted_info: Dict[str, Any] = {}
    booking: Optional[Dict[str, Any]] = None
    conversation_phase: str = "greeting"  # greeting, info_gathering, booking, confirmation

class VoiceMessageSchema(BaseModel):
    session_id: str
    text: str
    type: str  # "user_speech" or "agent_response"
    is_final: bool = True

class IntentDetectionSchema(BaseModel):
    intent: str
    confidence: float
    entities: Dict[str, Any] = {}
