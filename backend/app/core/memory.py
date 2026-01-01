import json
from typing import Dict, Any, Optional
from datetime import datetime
from app.models.schemas import ConversationStateSchema, MessageSchema
from uuid import uuid4

class ConversationMemory:
    """In-memory conversation state manager"""
    
    def __init__(self):
        self.sessions: Dict[str, ConversationStateSchema] = {}
    
    def create_session(self) -> str:
        """Create a new conversation session"""
        session_id = str(uuid4())
        self.sessions[session_id] = ConversationStateSchema(
            session_id=session_id,
            messages=[],
            conversation_phase="greeting"
        )
        return session_id
    
    def add_message(self, session_id: str, role: str, content: str):
        """Add a message to conversation history"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        message = MessageSchema(
            role=role,
            content=content,
            timestamp=datetime.now()
        )
        self.sessions[session_id].messages.append(message)
    
    def get_session(self, session_id: str) -> Optional[ConversationStateSchema]:
        """Get session state"""
        return self.sessions.get(session_id)
    
    def update_user_profile(self, session_id: str, **kwargs):
        """Update user profile info"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        for key, value in kwargs.items():
            if hasattr(self.sessions[session_id].user_profile, key):
                setattr(self.sessions[session_id].user_profile, key, value)
    
    def update_extracted_info(self, session_id: str, key: str, value: Any):
        """Update extracted conversation info"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        self.sessions[session_id].extracted_info[key] = value
    
    def set_current_intent(self, session_id: str, intent: str):
        """Set the current conversation intent"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        self.sessions[session_id].current_intent = intent
    
    def set_conversation_phase(self, session_id: str, phase: str):
        """Set conversation phase"""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")
        
        self.sessions[session_id].conversation_phase = phase
    
    def get_conversation_history(self, session_id: str) -> str:
        """Get formatted conversation history for LLM context"""
        if session_id not in self.sessions:
            return ""
        
        messages = self.sessions[session_id].messages
        history = ""
        for msg in messages:
            role = "Patient" if msg.role == "user" else "Assistant Anna"
            history += f"{role}: {msg.content}\n"
        return history

# Global memory instance
memory = ConversationMemory()
