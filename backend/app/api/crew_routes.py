"""API Routes for CrewAI Integration"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, Any, Optional, List

from ..core.session_manager import session_manager

router = APIRouter(prefix="/api/crew", tags=["CrewAI"])

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    session_id: str
    message: str

class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str
    state: str
    extracted_info: Dict[str, Any]
    selected_service: Optional[Dict[str, Any]]
    conversation_history: List[Dict[str, str]]

class SessionResponse(BaseModel):
    """Response model for session creation."""
    session_id: str
    message: str

@router.post("/session/new", response_model=SessionResponse)
async def create_new_session():
    """
    Create a new patient session with CrewAI agents.
    
    Returns:
        Session ID and welcome message
    """
    try:
        session_id = session_manager.create_session()
        
        return SessionResponse(
            session_id=session_id,
            message="Session created successfully. You can now start chatting with Anna, your medical assistant."
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat_with_crew(request: ChatRequest):
    """
    Send message to CrewAI agents and get response.
    
    Args:
        request: Chat request with session ID and message
        
    Returns:
        AI response with updated conversation state
    """
    # Get session
    crew = session_manager.get_session(request.session_id)
    
    if not crew:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Please create a new session."
        )
    
    try:
        # Process message through crew
        result = crew.process_message(request.message)
        
        return ChatResponse(
            response=result.get("response", ""),
            state=result.get("state", "unknown"),
            extracted_info=result.get("extracted_info", {}),
            selected_service=result.get("selected_service"),
            conversation_history=result.get("conversation_history", [])
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/session/{session_id}/state")
async def get_session_state(session_id: str):
    """
    Get current state of a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Complete session state
    """
    crew = session_manager.get_session(session_id)
    
    if not crew:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return crew.get_session_state()

@router.post("/session/{session_id}/reset")
async def reset_session(session_id: str):
    """
    Reset a session to initial state.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success message
    """
    success = session_manager.reset_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session reset successfully"}

@router.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Success message
    """
    success = session_manager.delete_session(session_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return {"message": "Session deleted successfully"}

@router.get("/stats")
async def get_crew_stats():
    """
    Get statistics about active CrewAI sessions.
    
    Returns:
        Session statistics
    """
    return {
        "active_sessions": session_manager.get_active_sessions_count(),
        "framework": "CrewAI",
        "version": "0.86.0"
    }
