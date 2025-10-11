# Complete Setup Guide

This guide will walk you through setting up the Developer Assistant from scratch.

## Prerequisites

### Required Software

1. **Python 3.8+**
   - Download from: https://www.python.org/downloads/
   - Verify: `python --version`

2. **Node.js 16+**
   - Download from: https://nodejs.org/
   - Verify: `node --version` and `npm --version`

3. **Google Cloud SDK**
   - Download from: https://cloud.google.com/sdk/docs/install
   - Verify: `gcloud --version`

### GCP Setup

1. **Create a GCP Project** (if you don't have one)
   ```bash
   gcloud projects create YOUR-PROJECT-ID
   gcloud config set project YOUR-PROJECT-ID
   ```

2. **Enable Vertex AI API**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

3. **Authenticate**
   ```bash
   gcloud auth application-default login
   ```

## Installation Steps

### Step 1: Clone/Download the Project

```bash
cd c:\Users\gaura\Downloads\repo\myaiagent
```

### Step 2: Configure Environment Variables

1. Open `.env` file
2. Update the following values:
   ```env
   GCP_PROJECT_ID=your-actual-project-id
   GCP_LOCATION=us-central1
   VERTEX_MODEL_NAME=text-bison@002
   PROJECT_ROOT=.
   ```

### Step 3: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 4: Install UI Dependencies

```bash
cd ui
npm install
cd ..
```

### Step 5: Test the Setup

Run the diagnostic script:
```bash
python diagnose.py
```

This will check:
- ✓ Environment variables
- ✓ GCP authentication
- ✓ Vertex AI access
- ✓ Model availability

## Running the Application

### Option 1: Using the Start Script (Windows)

Simply double-click `start.bat` or run:
```bash
start.bat
```

This will start both the backend and frontend automatically.

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
uvicorn main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd ui
npm run dev
```

## Accessing the Application

- **Web UI**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## First Steps

1. Open http://localhost:3000 in your browser
2. A session will be created automatically
3. Try your first query:
   ```
   Create a Python file called hello.py with a function that prints "Hello, World!"
   ```
4. View the thought process to see how the agent works
5. Continue the conversation - the agent remembers context!

## Configuration Options

### Adjust File Size Limits

In `tools/file_operations.py`:
```python
FileOperations(root_dir=".", max_file_size_mb=10)  # Change from 5MB to 10MB
```

### Change Session Timeout

In `main.py`:
```python
session_manager = SessionManager(session_timeout_minutes=120)  # 2 hours
```

### Use Different Model

In `.env`:
```env
VERTEX_MODEL_NAME=gemini-pro  # More capable model
```

### Change Project Root

In `.env`:
```env
PROJECT_ROOT=C:\Users\gaura\MyProjects  # Absolute path
# or
PROJECT_ROOT=../another-project  # Relative path
```

## Troubleshooting

### Backend Won't Start

1. Check Python version: `python --version` (should be 3.8+)
2. Verify dependencies: `pip list`
3. Check `.env` file exists and has correct values
4. Run diagnostics: `python diagnose.py`

### Frontend Won't Start

1. Check Node version: `node --version` (should be 16+)
2. Verify npm: `npm --version`
3. Reinstall dependencies: `cd ui && npm install`
4. Check port 3000 is available

### Authentication Errors

```bash
# Re-authenticate
gcloud auth application-default login

# Verify authentication
gcloud auth application-default print-access-token
```

### Model Not Available

```bash
# List available models
gcloud ai models list --region=us-central1

# Try different model in .env
VERTEX_MODEL_NAME=text-bison@001
```

### CORS Errors

The backend is configured to allow all origins. If you still see CORS errors:
1. Ensure backend is running on port 8000
2. Check the proxy configuration in `ui/vite.config.js`
3. Try accessing directly: http://localhost:8000/health

## Development Tips

### Hot Reload

Both backend and frontend support hot reload:
- **Backend**: Automatically reloads when you edit Python files
- **Frontend**: Automatically refreshes when you edit React files

### Viewing Logs

- **Backend logs**: Visible in the terminal running uvicorn
- **Frontend logs**: Open browser DevTools (F12) → Console

### API Testing

Use the interactive API docs at http://localhost:8000/docs to test endpoints directly.

## Production Deployment

### Backend

1. Set `DEBUG=False` in `.env`
2. Use a production ASGI server:
   ```bash
   pip install gunicorn
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

### Frontend

1. Build the production bundle:
   ```bash
   cd ui
   npm run build
   ```

2. Serve the `dist` folder with any static file server

### Security Considerations

- Add authentication/authorization
- Restrict CORS origins
- Use HTTPS
- Set up proper file permissions
- Use environment-specific `.env` files
- Enable rate limiting

## Getting Help

1. Check `TROUBLESHOOTING.md` for common issues
2. Run `python diagnose.py` for system diagnostics
3. Check `/health` endpoint for configuration status
4. Review logs in both terminals
5. Check the session history for agent's actions

## Next Steps

- Explore the API documentation at http://localhost:8000/docs
- Read `TROUBLESHOOTING.md` for common issues
- Check out example queries in the UI welcome screen
- Customize the agent's prompt in `agent/developer_agent.py`
- Add new tools in `tools/file_operations.py`

Enjoy using your Developer Assistant! 🚀
