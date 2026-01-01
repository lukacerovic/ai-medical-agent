from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.memory import memory
from app.agents.medical_agent import MedicalAgent
from datetime import datetime

router = APIRouter()
agent = MedicalAgent()

class ChatMessage(BaseModel):
    session_id: str
    text: str

@router.post("/chat")
async def chat(message: ChatMessage):
    """Send a chat message and get AI response"""
    try:
        print(f"Chat request received: {message.session_id}")
        
        # Get or create session
        session = memory.get_session(message.session_id)
        if not session:
            print(f"Creating new session: {message.session_id}")
            memory.create_session(message.session_id)
        
        # Process user input through agent
        print(f"Processing user input: {message.text}")
        response = await agent.process_user_input(message.session_id, message.text)
        
        print(f"Agent response: {response}")
        
        return {
            "session_id": message.session_id,
            "user_message": message.text,
            "assistant_response": response,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"ERROR in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))
