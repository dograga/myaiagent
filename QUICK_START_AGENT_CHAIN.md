# Quick Start - Agent Chain & Streaming

## What's New?

🎉 **Two-Agent Chain System** with real-time streaming!

- **Developer Agent** - Executes your requests
- **Dev Lead Agent** - Reviews the work for quality
- **Streaming UI** - See progress in real-time

---

## Start the System

### 1. Start Backend

```bash
cd c:\Users\gaura\Downloads\repo\myaiagent
uvicorn main:app --reload
```

**Expected output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

---

### 2. Start Frontend

```bash
cd ui
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
```

---

### 3. Open UI

Navigate to: `http://localhost:5173`

---

## Using the New Features

### Toggle Controls

You'll see three new toggles:

1. **Show Thought Process** ✓ (existing)
2. **👔 Dev Lead Review** ✓ (NEW)
3. **⚡ Streaming** ✓ (NEW)

---

### Example 1: Create a File with Review

**Enable:** ✓ Streaming, ✓ Dev Lead Review

**Type:**
```
Create a Python file with a hello function
```

**You'll see:**
```
⚙️ Status: 🔍 Analyzing requirements...
⚙️ Status: 📋 Creating action plan...
⚙️ Status: ⚙️ Executing actions...
🤖 Assistant: File hello.py created successfully
⚙️ Status: 👔 Dev Lead reviewing changes...
👔 Dev Lead Review
Decision: APPROVED
Comments:
- Function follows Python conventions
- Code is clean and readable
✅ Task completed
```

---

### Example 2: Modify Code with Review

**Type:**
```
Add error handling to the get_data function in api.py
```

**You'll see:**
```
⚙️ Status: 🔍 Analyzing requirements...
⚙️ Status: read_file: api.py
⚙️ Status: modify_code_block: Adding try-except...
🤖 Assistant: Added error handling with logging
👔 Dev Lead Review
Decision: APPROVED
Comments:
- Good use of specific exceptions
- Error messages are descriptive
- Proper logging implemented
✅ Task completed
```

---

### Example 3: Review Requests Improvements

**Type:**
```
Create a function to validate user input
```

**Possible review:**
```
👔 Dev Lead Review
Decision: NEEDS_IMPROVEMENT
Issues:
- Missing input validation for edge cases
- No docstring
- No type hints
Suggestions:
- Add validation for None and empty strings
- Include docstring with parameter descriptions
- Add type annotations
```

---

## API Usage

### Streaming Endpoint

```bash
curl -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create a Python file with a hello function",
    "show_details": true,
    "enable_review": true
  }'
```

**Response:** NDJSON stream
```
{"type":"status","message":"🔍 Analyzing requirements..."}
{"type":"status","message":"📋 Creating action plan..."}
{"type":"developer_result","response":"File created"}
{"type":"review","review":{"decision":"approved"}}
{"type":"complete","message":"✅ Task completed"}
```

---

### Traditional Endpoint

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create a Python file",
    "show_details": true,
    "enable_review": true,
    "stream": false
  }'
```

**Response:** JSON
```json
{
  "status": "success",
  "response": "File created successfully",
  "thought_process": [...],
  "review": {
    "status": "approved",
    "decision": "approved",
    "summary": "Changes look good"
  }
}
```

---

## Features

### ✅ Real-Time Progress
See what the agent is doing as it happens

### ✅ Quality Assurance
Dev Lead reviews every change

### ✅ Transparency
Understand the agent's reasoning

### ✅ Toggle Controls
Enable/disable features as needed

---

## Troubleshooting

### Backend Not Starting

**Error:** `Failed to initialize VertexAI`

**Fix:**
```bash
gcloud auth application-default login
```

---

### UI Not Connecting

**Error:** `Failed to create session`

**Fix:**
1. Check backend is running on port 8000
2. Check `.env` file has correct settings
3. Restart both backend and frontend

---

### No Review Showing

**Check:**
1. "👔 Dev Lead Review" toggle is enabled
2. Request actually made changes (not just read operations)
3. Backend logs for errors

---

## What to Try

### 1. Create Files
```
Create a Python file with a calculator class
```

### 2. Modify Code
```
Add docstrings to all functions in calculator.py
```

### 3. Complex Tasks
```
Create a REST API endpoint for user authentication
```

### 4. Review Quality
```
Create a function without error handling
```
(Dev Lead should request improvements)

---

## Next Steps

1. **Try different tasks** - See how the agent chain works
2. **Toggle features** - Compare streaming vs traditional
3. **Review feedback** - Learn from Dev Lead comments
4. **Iterate** - Use review feedback to improve

---

**Enjoy your new AI development team!** 🚀

Developer Agent + Dev Lead Agent = Better Code Quality
