from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv
from agent.developer_agent import DeveloperAgent
from session_manager import SessionManager

# Load environment variables
load_dotenv()

app = FastAPI(title="Developer Assistant API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize the agent and session manager
agent = DeveloperAgent(project_root=os.getcwd())
session_manager = SessionManager(session_timeout_minutes=60)

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    show_details: bool = True

@app.get("/health")
async def health_check():
    """Check if the service is properly configured and ready."""
    issues = []
    warnings = []
    
    # Check GCP project ID
    if not os.getenv("GCP_PROJECT_ID"):
        issues.append("GCP_PROJECT_ID not set in .env file")
    
    # Check GCP location
    if not os.getenv("GCP_LOCATION"):
        warnings.append("GCP_LOCATION not set (will default to us-central1)")
    
    # Check if ADC is configured
    adc_path = os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    if os.name == 'nt':  # Windows
        adc_path = os.path.expandvars("%APPDATA%\\gcloud\\application_default_credentials.json")
    
    if not os.path.exists(adc_path):
        issues.append(
            "Application Default Credentials not found. "
            "Please run: gcloud auth application-default login"
        )
    
    if issues:
        return {
            "status": "unhealthy",
            "ready": False,
            "issues": issues,
            "warnings": warnings,
            "message": "Service is not properly configured. Please check your .env file and authenticate with GCP."
        }
    
    response = {
        "status": "healthy",
        "ready": True,
        "message": "Service is ready to accept queries",
        "config": {
            "project": os.getenv("GCP_PROJECT_ID"),
            "location": os.getenv("GCP_LOCATION", "us-central1")
        }
    }
    
    if warnings:
        response["warnings"] = warnings
    
    return response

@app.post("/session/create")
async def create_session():
    """Create a new chat session."""
    session_id = session_manager.create_session()
    return {
        "status": "success",
        "session_id": session_id,
        "message": "New session created"
    }

@app.get("/session/{session_id}")
async def get_session_info(session_id: str):
    """Get information about a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    return {
        "status": "success",
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "last_accessed": session.last_accessed.isoformat(),
        "message_count": len(session.messages)
    }

@app.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """Get the chat history for a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    return {
        "status": "success",
        "session_id": session_id,
        "messages": session.get_history()
    }

@app.delete("/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    if session_manager.delete_session(session_id):
        return {"status": "success", "message": "Session deleted"}
    else:
        raise HTTPException(status_code=404, detail="Session not found")

@app.post("/session/{session_id}/clear")
async def clear_session_history(session_id: str):
    """Clear the history of a session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or expired")
    
    session.clear_history()
    return {"status": "success", "message": "Session history cleared"}

@app.get("/sessions")
async def list_sessions():
    """List all active sessions."""
    return {
        "status": "success",
        "active_sessions": session_manager.get_active_sessions_count(),
        "sessions": session_manager.list_sessions()
    }

@app.post("/query")
async def process_query(request: QueryRequest):
    """
    Process a natural language query with the developer agent.
    The agent is a coding assistant that can help with various development tasks.
    
    If session_id is provided, the conversation history will be maintained.
    If show_details is True, the response will include the agent's thought process.
    """
    try:
        # Get or create session
        session_id = request.session_id
        if session_id:
            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found or expired. Please create a new session.")
        else:
            # Create a new session if none provided
            session_id = session_manager.create_session()
            session = session_manager.get_session(session_id)
        
        # Add user message to history
        session.add_message("user", request.query)
        
        # Process the query
        if request.show_details:
            result = agent.run(request.query, return_details=True)
            
            # Extract detailed information
            response_text = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Format the thought process
            thought_process = []
            for step in intermediate_steps:
                action, observation = step
                thought_process.append({
                    "action": action.tool,
                    "action_input": action.tool_input,
                    "observation": str(observation),
                    "reasoning": action.log
                })
            
            # Add assistant response to history
            session.add_message("assistant", response_text)
            
            return {
                "status": "success",
                "session_id": session_id,
                "response": response_text,
                "thought_process": thought_process,
                "message_count": len(session.messages)
            }
        else:
            response = agent.run(request.query)
            session.add_message("assistant", response)
            
            return {
                "status": "success",
                "session_id": session_id,
                "response": response,
                "message_count": len(session.messages)
            }
            
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Configuration error: {str(e)}. Please ensure GCP credentials are properly configured."
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Service initialization error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
