# Troubleshooting Guide

## Common Issues and Solutions

### 1. Invalid JSON Input Error

**Error:**
```
{'status': 'error', 'message': 'Invalid JSON format. Error: ...'}
```

**Cause:** The agent is not formatting JSON correctly for `write_file` or `append_to_file` operations.

**Solution:** 
The agent prompt now includes:
- Explicit JSON format examples
- Clear error messages with correct format
- Tool descriptions emphasizing ONE LINE JSON format

**Correct Format:**
```json
{"file_path": "test.py", "content": "def hello():\n    print('Hello')"}
```

**What to Do:**
1. **Restart the server** to load updated prompts:
   ```bash
   uvicorn main:app --reload
   ```

2. **Create a new session** for clean state:
   ```bash
   curl -X POST http://localhost:8000/session/create
   ```

3. **Be specific in requests:**
   ```
   ✅ "Create a file called test.py with a hello function"
   ❌ "Can you help me with a file?"
   ```

**See:** `JSON_FORMAT_GUIDE.md` for detailed examples and troubleshooting.

---

### 2. "Input should be a valid string" Error with List Response

**Error:**
```
1 validation error for Generation
text
  Input should be a valid string [type=string_type, input_value=[...], input_type=list]
```

**Cause:** The VertexAI model is returning a list instead of a string, which causes validation errors in LangChain.

**Solution:** The agent now includes an LLM wrapper that automatically converts list responses to strings. This is handled in `_create_llm_wrapper()`.

**Additional Steps:**
- Increased `max_output_tokens` from 1024 to 2048 for complex projects
- Added output validation to ensure string responses

---

### 2. Reading Large or Complex Files

**Issue:** Agent fails when reading very large files or complex projects.

**Solutions Implemented:**

1. **File Size Limit:** Files larger than 5MB will return an error message suggesting alternative approaches
2. **Content Truncation:** Files with more than 50,000 characters are automatically truncated
3. **Binary File Detection:** Binary files are detected and rejected with a clear error message
4. **Encoding Handling:** UTF-8 encoding with fallback error handling

**Configuration:**
```python
# In agent initialization
file_ops = FileOperations(root_dir=".", max_file_size_mb=5)
```

---

### 3. Session Timeout Issues

**Issue:** Session expires during long operations.

**Solution:** Sessions automatically expire after 60 minutes of inactivity. For long-running operations:

```python
# Extend session timeout in main.py
session_manager = SessionManager(session_timeout_minutes=120)  # 2 hours
```

---

### 4. Model Not Available (404 Error)

**Symptoms:**
- HTTP 404 errors when initializing the agent
- "Model not found" messages

**Solutions:**

1. **Check Model Availability:**
   ```bash
   gcloud ai models list --region=us-central1
   ```

2. **Try Different Models:**
   Update `.env`:
   ```
   VERTEX_MODEL_NAME=text-bison@002
   # or
   VERTEX_MODEL_NAME=gemini-pro
   ```

3. **Enable Vertex AI API:**
   ```bash
   gcloud services enable aiplatform.googleapis.com --project=YOUR_PROJECT_ID
   ```

---

### 5. Authentication Errors

**Issue:** "Permission denied" or "Credentials not found"

**Solutions:**

1. **Re-authenticate:**
   ```bash
   gcloud auth application-default login
   ```

2. **Verify Credentials:**
   ```bash
   gcloud auth application-default print-access-token
   ```

3. **Check Project:**
   ```bash
   gcloud config get-value project
   ```

---

### 6. Agent Not Following Format

**Issue:** Agent gives direct responses instead of using "Final Answer:" format.

**Solution:** The `CustomOutputParser` now has fallback handling:
- If the output contains "Final Answer:", it's parsed as a final answer
- If it contains "Action:" and "Action Input:", it's parsed as an action
- Otherwise, it's treated as a final answer (fallback)

This prevents parsing errors while maintaining the expected format.

---

### 7. JSON Parsing Errors in Tool Calls

**Issue:** Agent fails to call `write_file` or `append_to_file` with proper JSON format.

**Solution:** Tool wrappers now include:
- JSON validation with clear error messages
- Automatic handling of malformed JSON
- Helpful error messages showing the expected format

**Example Error Response:**
```json
{
  "status": "error",
  "message": "Invalid JSON input. Expected format: {\"file_path\": \"path\", \"content\": \"text\"}"
}
```

---

## Diagnostic Tools

### Run Full Diagnostics

```bash
python diagnose.py
```

This will check:
- Environment variables
- Application Default Credentials
- gcloud CLI installation
- Vertex AI API access
- Available models
- LLM connectivity

### Check Service Health

```bash
curl http://localhost:8000/health
```

### View Active Sessions

```bash
curl http://localhost:8000/sessions
```

---

## Best Practices

### 1. Working with Large Files

Instead of reading entire large files:
```json
{
  "query": "Read the first 100 lines of large_file.py"
}
```

Or work with specific sections:
```json
{
  "query": "List all Python files in the project, then read only the main.py file"
}
```

### 2. Complex Operations

Break down complex operations into steps:
```json
// Step 1
{"query": "List all files in the src directory"}

// Step 2
{"query": "Read the config.py file from src"}

// Step 3
{"query": "Update the database connection string in config.py"}
```

### 3. Session Management

- Create a new session for each logical conversation
- Clear history when switching contexts
- Delete sessions when done to free resources

---

## Performance Optimization

### 1. Adjust Token Limits

For simpler tasks, reduce token usage:
```python
# In .env
VERTEX_MODEL_NAME=text-bison@001  # Faster, cheaper
```

For complex tasks, use more capable models:
```python
# In .env
VERTEX_MODEL_NAME=gemini-pro  # More capable
```

### 2. Disable Detailed Responses

For faster responses without thought process:
```json
{
  "query": "Your query here",
  "show_details": false
}
```

### 3. Session Cleanup

Regularly clean up expired sessions:
```python
# This happens automatically, but you can also manually trigger
session_manager.cleanup_expired_sessions()
```

---

## Getting Help

If you encounter issues not covered here:

1. Check the logs (FastAPI will show detailed error messages)
2. Run `python diagnose.py` for system diagnostics
3. Check the `/health` endpoint for configuration issues
4. Review the session history to see what the agent attempted
5. Try with `show_details: true` to see the agent's thought process
