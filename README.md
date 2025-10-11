# Developer Assistant AI Agent

A LangChain-based developer assistant that helps with code-related tasks using natural language processing powered by Google's Vertex AI.

## Features

- **Natural language processing** for developer tasks using Vertex AI
- **File operations** (read, write, append, delete)
- **Directory listing**
- **Session-based chat** with conversation history
- **Detailed thought process** - See how the agent reasons and makes decisions
- **Context-aware interactions** - Agent remembers previous messages in a session
- **Auto-approve mode** - Agent executes changes immediately (default) or waits for approval
- **FastAPI-based REST API** with comprehensive endpoints
- **Automatic session cleanup** - Sessions expire after 60 minutes of inactivity

## Prerequisites

- Python 3.8+
- GCP account with Vertex AI enabled
- Google Cloud SDK (gcloud CLI) installed
- Authenticated with Application Default Credentials

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd myaiagent
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Authenticate with GCP using Application Default Credentials:
   ```bash
   gcloud auth application-default login
   ```

5. Set up environment variables:
   - Update the `.env` file with your GCP project details

## Configuration

Update the `.env` file with your GCP project details:

```env
# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1

# Application Settings
PROJECT_ROOT=.
DEBUG=True
```

### Authentication

This application uses **Application Default Credentials (ADC)** for GCP authentication. This is more secure than using service account keys.

**Setup Steps:**

1. Install the Google Cloud SDK if you haven't already:
   - [Download gcloud CLI](https://cloud.google.com/sdk/docs/install)

2. Authenticate with your GCP account:
   ```bash
   gcloud auth application-default login
   ```

3. Set your default project (optional):
   ```bash
   gcloud config set project YOUR_PROJECT_ID
   ```

4. Ensure Vertex AI API is enabled:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

## Running the Application

### Backend (FastAPI)

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend (React UI)

1. Navigate to the UI directory:
   ```bash
   cd ui
   ```

2. Install dependencies (first time only):
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

The UI will be available at `http://localhost:3000`

**Note:** Both backend and frontend must be running for the full application to work.

## API Endpoints

### Health & Status
- `GET /health` - Check service health and configuration

### Session Management
- `POST /session/create` - Create a new chat session
- `GET /session/{session_id}` - Get session information
- `GET /session/{session_id}/history` - Get chat history for a session
- `DELETE /session/{session_id}` - Delete a session
- `POST /session/{session_id}/clear` - Clear session history
- `GET /sessions` - List all active sessions

### Query Processing
- `POST /query` - Process a natural language query with the developer agent

## Example Usage

### Using cURL

```bash
# Check service health
curl -X GET "http://localhost:8000/health"

# Create a new session
curl -X POST "http://localhost:8000/session/create"
# Response: {"status": "success", "session_id": "abc-123-def", "message": "New session created"}

# Process a query with session (shows thought process)
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create a Python script that prints hello world",
    "session_id": "abc-123-def",
    "show_details": true
  }'

# Continue the conversation in the same session
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Now add a function to calculate fibonacci numbers",
    "session_id": "abc-123-def"
  }'

# Get session history
curl -X GET "http://localhost:8000/session/abc-123-def/history"

# List all active sessions
curl -X GET "http://localhost:8000/sessions"

# Clear session history
curl -X POST "http://localhost:8000/session/abc-123-def/clear"

# Delete a session
curl -X DELETE "http://localhost:8000/session/abc-123-def"
```

### Python Example

```python
import requests

BASE_URL = "http://localhost:8000"

# Create a session
response = requests.post(f"{BASE_URL}/session/create")
session_id = response.json()["session_id"]
print(f"Session created: {session_id}")

# Send a query with detailed thought process
query_data = {
    "query": "Create a file called calculator.py with add and subtract functions",
    "session_id": session_id,
    "show_details": True
}

response = requests.post(f"{BASE_URL}/query", json=query_data)
result = response.json()

print(f"Response: {result['response']}")
print(f"\nThought Process:")
for step in result.get('thought_process', []):
    print(f"  Action: {step['action']}")
    print(f"  Input: {step['action_input']}")
    print(f"  Result: {step['observation']}")
    print()

# Continue the conversation
follow_up = {
    "query": "Add a multiply function to the same file",
    "session_id": session_id
}

response = requests.post(f"{BASE_URL}/query", json=follow_up)
print(f"Follow-up response: {response.json()['response']}")

# Get chat history
history = requests.get(f"{BASE_URL}/session/{session_id}/history")
print(f"\nChat History: {history.json()['messages']}")
```

## Architecture

The application consists of several main components:

1. **File Operations** (`tools/file_operations.py`): Handles all file system interactions
2. **Developer Agent** (`agent/developer_agent.py`): The main LangChain agent that processes natural language queries using Vertex AI
3. **Session Manager** (`session_manager.py`): Manages chat sessions and conversation history
4. **FastAPI Server** (`main.py`): Provides a REST API for interacting with the agent

## Key Features Explained

### Session-Based Chat

Each conversation is maintained in a session, allowing the agent to remember context:

```python
# First message
"Create a file called app.py with a hello function"

# Follow-up message (agent remembers the file)
"Add a goodbye function to the same file"
```

### Detailed Thought Process

When `show_details: true`, the response includes:
- **Actions taken**: Which tools the agent used
- **Action inputs**: The parameters passed to each tool
- **Observations**: The results from each tool
- **Reasoning**: The agent's thought process

Example response:
```json
{
  "status": "success",
  "session_id": "abc-123",
  "response": "I've created the file with the requested functions.",
  "thought_process": [
    {
      "action": "write_file",
      "action_input": "{\"file_path\": \"app.py\", \"content\": \"def hello():\\n    print('Hello!')\"}",
      "observation": "{\"status\": \"success\", \"message\": \"File app.py written successfully\"}",
      "reasoning": "Thought: I need to create a new file with the hello function..."
    }
  ],
  "message_count": 2
}
```

## Security Considerations

- Application Default Credentials are stored securely by gcloud and are not committed to version control
- The `.env` file should never be committed to version control (add it to `.gitignore`)
- Use appropriate file permissions for the project directory
- Consider adding authentication/authorization for the API endpoints in production
- In production, consider using Workload Identity or service accounts with minimal required permissions

## Troubleshooting

### Authentication Issues

If you get authentication errors:

1. Verify you're authenticated:
   ```bash
   gcloud auth application-default print-access-token
   ```

2. Re-authenticate if needed:
   ```bash
   gcloud auth application-default login
   ```

3. Check your project is set correctly:
   ```bash
   gcloud config get-value project
   ```

### Health Check

Before making queries, check the service health:
```bash
curl http://localhost:8000/health
```

This will show any configuration issues.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
