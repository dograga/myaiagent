# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Check

```bash
python --version   # Need 3.8+
node --version     # Need 16+
gcloud --version   # Need gcloud CLI
```

## Setup (First Time Only)

### 1. Configure GCP

```bash
gcloud auth application-default login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable aiplatform.googleapis.com
```

### 2. Update .env File

```env
GCP_PROJECT_ID=your-actual-project-id
GCP_LOCATION=us-central1
VERTEX_MODEL_NAME=text-bison@002
PROJECT_ROOT=.
```

### 3. Install Dependencies

```bash
# Python
pip install -r requirements.txt

# Node.js
cd ui
npm install
cd ..
```

## Run the Application

### Option 1: Windows Quick Start

```bash
start.bat
```

### Option 2: Manual Start

**Terminal 1:**
```bash
uvicorn main:app --reload
```

**Terminal 2:**
```bash
cd ui
npm run dev
```

## Access

- **UI**: http://localhost:3000
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs

## Test It

Open http://localhost:3000 and try:

```
Create a Python file called test.py with a hello world function
```

## Common Commands

```bash
# Check health
curl http://localhost:8000/health

# Run diagnostics
python diagnose.py

# Create session
curl -X POST http://localhost:8000/session/create

# Send query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "List all files", "show_details": true}'
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Auth error | `gcloud auth application-default login` |
| 404 model | Check `.env` has correct `GCP_PROJECT_ID` |
| Port in use | Change port in `main.py` or `vite.config.js` |
| UI won't load | Ensure backend is running first |

## Next Steps

- Read `SETUP_GUIDE.md` for detailed setup
- Check `TROUBLESHOOTING.md` for common issues
- Explore `PROJECT_SUMMARY.md` for architecture details

## Example Queries

```
Create a calculator.py file with add and subtract functions
```

```
Read the contents of main.py
```

```
Add a multiply function to calculator.py
```

```
List all Python files in the current directory
```

```
Delete the test.py file
```

That's it! You're ready to go! 🚀
