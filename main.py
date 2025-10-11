from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from agent.developer_agent import DeveloperAgent

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

# Initialize the agent
agent = DeveloperAgent(project_root=os.getcwd())

class QueryRequest(BaseModel):
    query: str

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

@app.post("/query")
async def process_query(request: QueryRequest):
    """
    Process a natural language query with the developer agent.
    The agent is a coding assistant that can help with various development tasks.
    """
    try:
        response = agent.run(request.query)
        return {"status": "success", "response": response}
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
