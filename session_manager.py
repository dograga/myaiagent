"""
Session manager for maintaining chat history across requests
"""
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import uuid
from dataclasses import dataclass, field
from threading import Lock

@dataclass
class ChatSession:
    """Represents a chat session with history."""
    session_id: str
    created_at: datetime
    last_accessed: datetime
    messages: List[Dict[str, str]] = field(default_factory=list)
    
    def add_message(self, role: str, content: str):
        """Add a message to the session history."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.last_accessed = datetime.now()
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get the message history."""
        return self.messages
    
    def clear_history(self):
        """Clear the message history."""
        self.messages.clear()

class SessionManager:
    """Manages chat sessions with automatic cleanup."""
    
    def __init__(self, session_timeout_minutes: int = 60):
        self.sessions: Dict[str, ChatSession] = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.lock = Lock()
    
    def create_session(self) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        with self.lock:
            self.sessions[session_id] = ChatSession(
                session_id=session_id,
                created_at=now,
                last_accessed=now
            )
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a session by ID, return None if not found or expired."""
        with self.lock:
            session = self.sessions.get(session_id)
            
            if session is None:
                return None
            
            # Check if session has expired
            if datetime.now() - session.last_accessed > self.session_timeout:
                del self.sessions[session_id]
                return None
            
            return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        with self.lock:
            if session_id in self.sessions:
                del self.sessions[session_id]
                return True
            return False
    
    def cleanup_expired_sessions(self):
        """Remove all expired sessions."""
        now = datetime.now()
        with self.lock:
            expired = [
                sid for sid, session in self.sessions.items()
                if now - session.last_accessed > self.session_timeout
            ]
            for sid in expired:
                del self.sessions[sid]
        
        return len(expired)
    
    def get_active_sessions_count(self) -> int:
        """Get the count of active sessions."""
        with self.lock:
            return len(self.sessions)
    
    def list_sessions(self) -> List[Dict[str, str]]:
        """List all active sessions with basic info."""
        with self.lock:
            return [
                {
                    "session_id": session.session_id,
                    "created_at": session.created_at.isoformat(),
                    "last_accessed": session.last_accessed.isoformat(),
                    "message_count": len(session.messages)
                }
                for session in self.sessions.values()
            ]
