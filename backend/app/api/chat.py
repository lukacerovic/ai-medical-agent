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
        print(f"\n" + "="*80)
        print(f"💬 [CHAT API] Chat request received")
        print(f"="*80)
        print(f"🎫 [CHAT API] Session ID: {message.session_id}")
        print(f"📝 [CHAT API] User message: {message.text}")
        
        # Get session (must already exist from /session/new)
        session = memory.get_session(message.session_id)
        if not session:
            print(f"❌ [CHAT API] ERROR: Session {message.session_id} not found!")
            print(f"⚠️ [CHAT API] User must call /session/new first")
            print("="*80 + "\n")
            raise HTTPException(
                status_code=404, 
                detail=f"Session {message.session_id} not found. Please create a session first via /session/new"
            )
        
        print(f"✅ [CHAT API] Session found")
        print(f"📊 [CHAT API] Messages in history: {len(session.messages)}")
        
        # Process user input through agent
        print(f"🤖 [CHAT API] Sending to AI agent...")
        print("="*80 + "\n")
        
        response = await agent.process_user_input(message.session_id, message.text)
        
        print(f"\n" + "="*80)
        print(f"✅ [CHAT API] AI response generated successfully")
        print(f"📝 [CHAT API] Response length: {len(response)} characters")
        print(f"📝 [CHAT API] Response preview: {response[:100]}...")
        print("="*80 + "\n")
        
        return {
            "session_id": message.session_id,
            "user_message": message.text,
            "assistant_response": response,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"\n" + "!"*80)
        print(f"❌ [CHAT API] ERROR: {e}")
        print("!"*80 + "\n")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
