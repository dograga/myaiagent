from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any, AsyncGenerator
import os
import json
import asyncio
import base64
from dotenv import load_dotenv
from agent.developer_agent import DeveloperAgent
from agent.dev_lead_agent import DevLeadAgent
from agent.devops_agent import DevOpsAgent
from agent.devops_lead_agent import DevOpsLeadAgent
from agent.cloud_architect_agent import CloudArchitectAgent
from session_manager import SessionManager
from utils.file_handler import FileHandler

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

# Initialize all agents
developer_agent = DeveloperAgent(project_root=project_root, auto_approve=auto_approve)
dev_lead_agent = DevLeadAgent()
devops_agent = DevOpsAgent(project_root=project_root, auto_approve=auto_approve)
devops_lead_agent = DevOpsLeadAgent()
cloud_architect_agent = CloudArchitectAgent(project_root=project_root, auto_approve=auto_approve)
session_manager = SessionManager(session_timeout_minutes=60)

class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    show_details: bool = True
    enable_review: bool = True  # Enable Lead review
    stream: bool = False  # Enable streaming
    agent_type: str = "developer"  # "developer", "devops", or "cloud_architect"
    attached_files: Optional[List[Dict[str, str]]] = None  # List of {filename, content}

class SettingsRequest(BaseModel):
    project_root: Optional[str] = None
    model_name: Optional[str] = None

class SettingsResponse(BaseModel):
    project_root: str
    model_name: str
    available_models: List[str]

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

def process_attached_files(attached_files: Optional[List[Dict[str, str]]]) -> tuple[str, List[str]]:
    """Process attached files and return formatted text and list of temp file paths.
    
    Returns:
        tuple: (formatted_text, temp_file_paths)
    """
    if not attached_files:
        return "", []
    
    formatted_text = "\n\n**Attached Files:**\n"
    temp_file_paths = []
    
    for file_info in attached_files:
        filename = file_info.get("filename", "unknown")
        content_base64 = file_info.get("content", "")
        
        try:
            # Validate and process the file
            file_type = FileHandler.validate_file_type(filename)
            
            # Decode base64 content
            file_content = base64.b64decode(content_base64)
            
            # Save to temp file
            temp_path = FileHandler.save_temp_file(file_content, filename)
            temp_file_paths.append(temp_path)
            
            # Extract text content based on file type
            if file_type == "pdf":
                text_content = FileHandler.extract_pdf_text(temp_path)
                formatted_text += f"\n--- File: {filename} (PDF) ---\n{text_content}\n"
            elif file_type == "image":
                formatted_text += f"\n--- File: {filename} (Image) ---\n[Image file attached - will be processed by AI model]\n"
            else:  # text file
                text_content = file_content.decode('utf-8', errors='ignore')
                formatted_text += f"\n--- File: {filename} ---\n{text_content}\n"
        
        except ValueError as e:
            formatted_text += f"\n--- File: {filename} (Error: {str(e)}) ---\n"
        except Exception as e:
            formatted_text += f"\n--- File: {filename} (Error processing file: {str(e)}) ---\n"
    
    return formatted_text, temp_file_paths

async def stream_agent_response(
    query: str,
    session_id: str,
    show_details: bool,
    enable_review: bool,
    agent_type: str = "developer"
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
        
        # Select the appropriate agent and lead
        if agent_type == "devops":
            agent = devops_agent
            lead_agent = devops_lead_agent
            agent_name = "DevOps Agent"
            lead_name = "DevOps Lead"
        elif agent_type == "cloud_architect":
            agent = cloud_architect_agent
            lead_agent = None  # Cloud Architect doesn't need review
            agent_name = "Cloud Architect"
            lead_name = None
        else:
            agent = developer_agent
            lead_agent = dev_lead_agent
            agent_name = "Developer Agent"
            lead_name = "Dev Lead"
        
        # Send execution status
        yield json.dumps({
            "type": "status",
            "message": f"⚙️ Executing {agent_name}..."
        }) + "\n"
        await asyncio.sleep(0.1)
        
        # Process the query
        # NOTE: agent.run() is synchronous and blocks, but we stream results after
        if show_details:
            try:
                result = agent.run(query, return_details=True)
                response_text = result.get("output", "")
                intermediate_steps = result.get("intermediate_steps", [])
                
                # Check if agent stopped due to iteration limit
                # If so, extract whatever output was generated
                if not response_text and intermediate_steps:
                    # Agent hit limit but did work - extract last observation
                    last_action, last_observation = intermediate_steps[-1]
                    response_text = f"Task partially completed. Last action: {last_action.tool}\nResult: {last_observation}"
                elif not response_text:
                    response_text = "Agent completed but no output was generated."
            except Exception as e:
                # If agent fails, try to extract intermediate steps
                error_msg = str(e)
                response_text = f"Agent encountered an issue: {error_msg}"
                intermediate_steps = []
                
                # Try to get partial results if available
                try:
                    if hasattr(agent.agent, 'intermediate_steps'):
                        intermediate_steps = agent.agent.intermediate_steps
                except:
                    pass
            
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
            
            # Lead Review - ALWAYS run if enabled and lead_agent exists
            if enable_review and lead_agent:
                yield json.dumps({
                    "type": "status",
                    "message": f"👔 {lead_name} reviewing changes..."
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
                review_result = lead_agent.review(
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
            try:
                response = agent.run(query)
                if not response:
                    response = "Agent completed but no output was generated."
            except Exception as e:
                response = f"Agent encountered an issue: {str(e)}"
            
            yield json.dumps({
                "type": "developer_result",
                "response": response
            }) + "\n"
            await asyncio.sleep(0.1)
            
            # Lead Review for non-detailed mode
            if enable_review and lead_agent:
                yield json.dumps({
                    "type": "status",
                    "message": f"👔 {lead_name} reviewing changes..."
                }) + "\n"
                await asyncio.sleep(0.1)
                
                review_result = lead_agent.review(
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
        
        # Process attached files
        file_text, temp_file_paths = process_attached_files(request.attached_files)
        formatted_query = request.query + file_text
        
        # Add user message to history
        session.add_message("user", formatted_query)
        
        # Clean up temp files after processing
        try:
            for temp_path in temp_file_paths:
                FileHandler.cleanup_temp_file(temp_path)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp files: {e}")
        
        return StreamingResponse(
            stream_agent_response(
                formatted_query,
                session_id,
                request.show_details,
                request.enable_review,
                request.agent_type
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
        
        # Process attached files
        file_text, temp_file_paths = process_attached_files(request.attached_files)
        formatted_query = request.query + file_text
        
        # Add user message to history
        session.add_message("user", formatted_query)
        
        # Select the appropriate agent and lead
        if request.agent_type == "devops":
            agent = devops_agent
            lead_agent = devops_lead_agent
        elif request.agent_type == "cloud_architect":
            agent = cloud_architect_agent
            lead_agent = None  # Cloud Architect doesn't need review
        else:
            agent = developer_agent
            lead_agent = dev_lead_agent
        
        # Process the query
        if request.show_details:
            try:
                result = agent.run(formatted_query, return_details=True)
                
                # Extract detailed information
                response_text = result.get("output", "")
                intermediate_steps = result.get("intermediate_steps", [])
                
                # Handle iteration limit case
                if not response_text and intermediate_steps:
                    last_action, last_observation = intermediate_steps[-1]
                    response_text = f"Task partially completed. Last action: {last_action.tool}\nResult: {last_observation}"
                elif not response_text:
                    response_text = "Agent completed but no output was generated."
            except Exception as e:
                # Extract whatever we can from failed execution
                response_text = f"Agent encountered an issue: {str(e)}"
                intermediate_steps = []
                try:
                    if hasattr(agent.agent, 'intermediate_steps'):
                        intermediate_steps = agent.agent.intermediate_steps
                except:
                    pass
            
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
            
            # Lead Review - run if enabled and lead_agent exists
            review_result = None
            if request.enable_review and lead_agent:
                actions_for_review = [
                    {
                        "action": action.tool,
                        "action_input": action.tool_input,
                        "observation": str(observation)
                    }
                    for action, observation in intermediate_steps
                ]
                
                review_result = lead_agent.review(
                    task=request.query,
                    actions=actions_for_review,
                    result=response_text
                )
            
            # Add assistant response to history
            session.add_message("assistant", response_text)
            
            # Clean up temp files
            try:
                for temp_path in temp_file_paths:
                    FileHandler.cleanup_temp_file(temp_path)
            except Exception as e:
                print(f"Warning: Failed to cleanup temp files: {e}")
            
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
            response = agent.run(formatted_query)
            session.add_message("assistant", response)
            
            # Clean up temp files
            try:
                for temp_path in temp_file_paths:
                    FileHandler.cleanup_temp_file(temp_path)
            except Exception as e:
                print(f"Warning: Failed to cleanup temp files: {e}")
            
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

@app.get("/settings", response_model=SettingsResponse)
async def get_settings():
    """Get current settings."""
    return SettingsResponse(
        project_root=developer_agent.project_root,
        model_name=os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash-exp"),
        available_models=[
            "gemini-2.0-flash-exp",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]
    )

@app.post("/settings")
async def update_settings(settings: SettingsRequest):
    """Update settings and reinitialize agents."""
    global developer_agent, dev_lead_agent, devops_agent, devops_lead_agent, cloud_architect_agent
    
    try:
        # Update project root if provided
        if settings.project_root:
            if not os.path.exists(settings.project_root):
                raise HTTPException(
                    status_code=400,
                    detail=f"Project root path does not exist: {settings.project_root}"
                )
            if not os.path.isabs(settings.project_root):
                settings.project_root = os.path.abspath(settings.project_root)
            
            # Update environment variable
            os.environ["PROJECT_ROOT"] = settings.project_root
            
            # Reinitialize all agents with new project root
            auto_approve = os.getenv("AUTO_APPROVE", "true").lower() in ("true", "1", "yes")
            developer_agent = DeveloperAgent(project_root=settings.project_root, auto_approve=auto_approve)
            devops_agent = DevOpsAgent(project_root=settings.project_root, auto_approve=auto_approve)
            cloud_architect_agent = CloudArchitectAgent(project_root=settings.project_root, auto_approve=auto_approve)
        
        # Update model name if provided
        if settings.model_name:
            valid_models = ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"]
            if settings.model_name not in valid_models:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid model name. Must be one of: {', '.join(valid_models)}"
                )
            
            # Update environment variable
            os.environ["VERTEX_MODEL_NAME"] = settings.model_name
            
            # Reinitialize all agents with new model
            # Use current agent's project_root to preserve any updates made in this session
            auto_approve = os.getenv("AUTO_APPROVE", "true").lower() in ("true", "1", "yes")
            current_project_root = developer_agent.project_root
            
            developer_agent = DeveloperAgent(project_root=current_project_root, auto_approve=auto_approve)
            dev_lead_agent = DevLeadAgent()
            devops_agent = DevOpsAgent(project_root=current_project_root, auto_approve=auto_approve)
            devops_lead_agent = DevOpsLeadAgent()
            cloud_architect_agent = CloudArchitectAgent(project_root=current_project_root, auto_approve=auto_approve)
        
        return {
            "status": "success",
            "message": "Settings updated successfully",
            "project_root": developer_agent.project_root,
            "model_name": os.getenv("VERTEX_MODEL_NAME", "gemini-2.0-flash-exp")
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error updating settings: {str(e)}"
        )

@app.get("/browse-directory")
async def browse_directory(path: Optional[str] = None):
    """Browse directories for project root selection."""
    try:
        # Default to user's home directory if no path provided
        if not path:
            path = os.path.expanduser("~")
        
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail="Path does not exist")
        
        if not os.path.isdir(path):
            raise HTTPException(status_code=400, detail="Path is not a directory")
        
        # Get parent directory
        parent = os.path.dirname(path) if path != os.path.dirname(path) else None
        
        # List directories
        items = []
        try:
            for item in sorted(os.listdir(path)):
                item_path = os.path.join(path, item)
                if os.path.isdir(item_path):
                    items.append({
                        "name": item,
                        "path": item_path,
                        "type": "directory"
                    })
        except PermissionError:
            pass
        
        return {
            "current_path": path,
            "parent_path": parent,
            "items": items
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error browsing directory: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
