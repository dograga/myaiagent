# Developer Assistant AI Agent

A LangChain-based developer assistant that helps with code-related tasks using natural language processing powered by Google's Vertex AI.

## Features

- Natural language processing for developer tasks using Vertex AI
- File operations (read, write, append, delete)
- Directory listing
- FastAPI-based REST API
- Conversation memory for context-aware interactions

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

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Endpoints

- `GET /health` - Check service health and configuration
- `POST /query` - Process a natural language query with the developer agent

## Example Usage

### Using cURL

```bash
# Check service health
curl -X GET "http://localhost:8000/health"

# Process a query
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a Python script that prints hello world"}'

# Ask the agent to create a file
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Write a function to calculate fibonacci numbers and save it to utils.py"}'

# Ask the agent to read a file
curl -X POST "http://localhost:8000/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "Read the contents of README.md"}'
```

## Architecture

The application consists of several main components:

1. **File Operations** (`tools/file_operations.py`): Handles all file system interactions
2. **Developer Agent** (`agent/developer_agent.py`): The main LangChain agent that processes natural language queries using Vertex AI
3. **FastAPI Server** (`main.py`): Provides a REST API for interacting with the agent

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
