"""Session Manager for Medical Crew Instances"""

from typing import Dict, Optional
import uuid
from datetime import datetime, timedelta
import threading
import time

from ..agents.medical_crew import MedicalCrew

class SessionManager:
    """
    Manages multiple patient session instances.
    Each session has its own crew instance with independent state.
    """
    
    def __init__(self, session_timeout_minutes: int = 30):
        """
        Initialize session manager.
        
        Args:
            session_timeout_minutes: Session expiry time in minutes
        """
        self.sessions: Dict[str, Dict] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.lock = threading.Lock()
        
        # Start cleanup thread
        self._start_cleanup_thread()
    
    def create_session(self) -> str:
        """
        Create a new patient session.
        
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        with self.lock:
            self.sessions[session_id] = {
                "crew": MedicalCrew(session_id),
                "created_at": datetime.now(),
                "last_activity": datetime.now(),
            }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[MedicalCrew]:
        """
        Get crew instance for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            MedicalCrew instance or None if not found
        """
        with self.lock:
            session = self.sessions.get(session_id)
            
            if session:
                # Update last activity
                session["last_activity"] = datetime.now()
                return session["crew"]
            
            return None
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
    
    def reset_session(self, session_id: str) -> bool:
        """
        Reset a session to initial state.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if reset, False if not found
        """
        crew = self.get_session(session_id)
        if crew:
            crew.reset_session()
            return True
        return False
    
    def get_active_sessions_count(self) -> int:
        """
        Get count of active sessions.
        
        Returns:
            Number of active sessions
        """
        with self.lock:
            return len(self.sessions)
    
    def _cleanup_expired_sessions(self):
        """
        Remove expired sessions.
        """
        now = datetime.now()
        expired = []
        
        with self.lock:
            for session_id, session in self.sessions.items():
                if now - session["last_activity"] > self.session_timeout:
                    expired.append(session_id)
            
            for session_id in expired:
                del self.sessions[session_id]
        
        if expired:
            print(f"Cleaned up {len(expired)} expired sessions")
    
    def _start_cleanup_thread(self):
        """
        Start background thread for cleanup.
        """
        def cleanup_loop():
            while True:
                time.sleep(300)  # Run every 5 minutes
                self._cleanup_expired_sessions()
        
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()

# Global session manager instance
session_manager = SessionManager(session_timeout_minutes=30)
