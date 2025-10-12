from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, AsyncGenerator
import os
import json
import asyncio
from dotenv import load_dotenv
from agent.developer_agent import DeveloperAgent
from agent.dev_lead_agent import DevLeadAgent
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
project_root = os.getenv("PROJECT_ROOT", os.getcwd())
if not os.path.isabs(project_root):
    project_root = os.path.abspath(project_root)

# Get auto-approve setting from environment (default: True)
auto_approve = os.getenv("AUTO_APPROVE", "true").lower() in ("true", "1", "yes")

agent = DeveloperAgent(project_root=project_root, auto_approve=auto_approve)
dev_lead_agent = DevLeadAgent()
session_manager = SessionManager(session_timeout_minutes=60)

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    show_details: bool = True
    enable_review: bool = True  # Enable Dev Lead review
    stream: bool = False  # Enable streaming

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
            "location": os.getenv("GCP_LOCATION", "us-central1"),
            "auto_approve": auto_approve,
            "project_root": project_root
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

async def stream_agent_response(
    query: str,
    session_id: str,
    show_details: bool,
    enable_review: bool
) -> AsyncGenerator[str, None]:
    """Stream the agent's response with progress updates."""
    try:
        # Send initial status
        yield json.dumps({
            "type": "status",
            "message": "🔍 Analyzing requirements..."
        }) + "\n"
        await asyncio.sleep(0.1)
        
        # Send planning status
        yield json.dumps({
            "type": "status",
            "message": "📋 Creating action plan..."
        }) + "\n"
        await asyncio.sleep(0.1)
        
        # Send execution status
        yield json.dumps({
            "type": "status",
            "message": "⚙️ Executing Developer Agent..."
        }) + "\n"
        await asyncio.sleep(0.1)
        
        # Process the query
        # NOTE: agent.run() is synchronous and blocks, but we stream results after
        if show_details:
            result = agent.run(query, return_details=True)
            response_text = result.get("output", "")
            intermediate_steps = result.get("intermediate_steps", [])
            
            # Stream each step as it was executed
            for i, step in enumerate(intermediate_steps):
                action, observation = step
                yield json.dumps({
                    "type": "step",
                    "step_number": i + 1,
                    "action": action.tool,
                    "action_input": str(action.tool_input)[:200],  # Truncate long inputs
                    "observation": str(observation)[:500]  # Truncate long observations
                }) + "\n"
                await asyncio.sleep(0.05)  # Small delay for UI to process
            
            # Send developer result
            yield json.dumps({
                "type": "developer_result",
                "response": response_text,
                "thought_process": [
                    {
                        "action": action.tool,
                        "action_input": action.tool_input,
                        "observation": str(observation),
                        "reasoning": action.log
                    }
                    for action, observation in intermediate_steps
                ]
            }) + "\n"
            await asyncio.sleep(0.1)
            
            # Dev Lead Review - ALWAYS run if enabled, even with no intermediate steps
            if enable_review:
                yield json.dumps({
                    "type": "status",
                    "message": "👔 Dev Lead reviewing changes..."
                }) + "\n"
                await asyncio.sleep(0.1)
                
                # Prepare review data
                actions_for_review = [
                    {
                        "action": action.tool,
                        "action_input": str(action.tool_input)[:200],
                        "observation": str(observation)[:500]
                    }
                    for action, observation in intermediate_steps
                ] if intermediate_steps else []
                
                # Run review
                review_result = dev_lead_agent.review(
                    task=query,
                    actions=actions_for_review,
                    result=response_text
                )
                
                yield json.dumps({
                    "type": "review",
                    "review": review_result
                }) + "\n"
                await asyncio.sleep(0.1)
        else:
            response = agent.run(query)
            yield json.dumps({
                "type": "developer_result",
                "response": response
            }) + "\n"
            await asyncio.sleep(0.1)
            
            # Dev Lead Review for non-detailed mode
            if enable_review:
                yield json.dumps({
                    "type": "status",
                    "message": "👔 Dev Lead reviewing changes..."
                }) + "\n"
                await asyncio.sleep(0.1)
                
                review_result = dev_lead_agent.review(
                    task=query,
                    actions=[],
                    result=response
                )
                
                yield json.dumps({
                    "type": "review",
                    "review": review_result
                }) + "\n"
                await asyncio.sleep(0.1)
        
        # Send completion
        yield json.dumps({
            "type": "complete",
            "message": "✅ Task completed"
        }) + "\n"
        
    except Exception as e:
        import traceback
        yield json.dumps({
            "type": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }) + "\n"


@app.post("/query/stream")
async def process_query_stream(request: QueryRequest):
    """
    Stream the agent's response with real-time updates.
    """
    try:
        # Get or create session
        session_id = request.session_id
        if session_id:
            session = session_manager.get_session(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found or expired")
        else:
            session_id = session_manager.create_session()
            session = session_manager.get_session(session_id)
        
        # Add user message to history
        session.add_message("user", request.query)
        
        return StreamingResponse(
            stream_agent_response(
                request.query,
                session_id,
                request.show_details,
                request.enable_review
            ),
            media_type="application/x-ndjson"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query")
async def process_query(request: QueryRequest):
    """
    Process a natural language query with the developer agent.
    The agent is a coding assistant that can help with various development tasks.
    
    If session_id is provided, the conversation history will be maintained.
    If show_details is True, the response will include the agent's thought process.
    If enable_review is True, the Dev Lead will review the changes.
    If stream is True, use /query/stream endpoint instead.
    """
    if request.stream:
        return await process_query_stream(request)
    
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
            
            # Dev Lead Review
            review_result = None
            if request.enable_review and intermediate_steps:
                actions_for_review = [
                    {
                        "action": action.tool,
                        "action_input": action.tool_input,
                        "observation": str(observation)
                    }
                    for action, observation in intermediate_steps
                ]
                
                review_result = dev_lead_agent.review(
                    task=request.query,
                    actions=actions_for_review,
                    result=response_text
                )
            
            # Add assistant response to history
            session.add_message("assistant", response_text)
            
            response_data = {
                "status": "success",
                "session_id": session_id,
                "response": response_text,
                "thought_process": thought_process,
                "message_count": len(session.messages)
            }
            
            if review_result:
                response_data["review"] = review_result
            
            return response_data
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
