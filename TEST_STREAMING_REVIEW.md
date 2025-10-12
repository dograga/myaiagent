# Test Guide - Streaming & Dev Lead Review

## Quick Start

### 1. Start Backend
```bash
cd c:\Users\gaura\Downloads\repo\myaiagent
uvicorn main:app --reload
```

**Expected:**
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

**Expected:**
```
VITE ready in xxx ms
➜  Local:   http://localhost:5173/
```

---

### 3. Open Browser
Navigate to: `http://localhost:5173`

---

## Test Cases

### Test 1: Basic Streaming with Review ✅

**Setup:**
- ✓ Show Thought Process
- ✓ 👔 Dev Lead Review
- ✓ ⚡ Streaming

**Input:**
```
Create a Python file called hello.py with a hello function
```

**Expected Output:**

**Phase 1: Status Updates (instant)**
```
⚙️ Status: 🔍 Analyzing requirements...
```
*(updates to)*
```
⚙️ Status: 📋 Creating action plan...
```
*(updates to)*
```
⚙️ Status: ⚙️ Executing Developer Agent...
```

**Phase 2: Pause (agent working)**
- Brief pause while agent executes

**Phase 3: Steps Stream (fast)**
```
⚙️ Status: Step 1: write_file - {"file_path": "hello.py", "content": "def hello():\n    print('Hello')\n"}
```

**Phase 4: Developer Result**
```
🤖 Assistant
File hello.py created successfully with a hello function.

🧠 Thought Process (1 steps)
[Expandable details]
```

**Phase 5: Dev Lead Review**
```
⚙️ Status: 👔 Dev Lead reviewing changes...
```
*(updates to)*
```
👔 Dev Lead Review
Decision: APPROVED
Summary: Code meets requirements and follows best practices
Comments:
- Function structure is correct
- Follows Python naming conventions
```

**Phase 6: Final State**
```
👤 You: Create a Python file called hello.py with a hello function
🤖 Assistant: File hello.py created successfully
👔 Dev Lead Review: APPROVED - Code meets requirements
```

✅ **Pass if:** All phases appear in order, Dev Lead review shows

---

### Test 2: Non-Streaming Mode ✅

**Setup:**
- ✓ Show Thought Process
- ✓ 👔 Dev Lead Review
- ✗ ⚡ Streaming (DISABLED)

**Input:**
```
Create a Python file called test.py
```

**Expected Output:**

**Immediate (no streaming):**
```
👤 You: Create a Python file called test.py
🤖 Assistant: File test.py created successfully
👔 Dev Lead Review: APPROVED - ...
```

✅ **Pass if:** No status messages, direct result, review still appears

---

### Test 3: Review Without Tools ✅

**Setup:**
- ✓ Show Thought Process
- ✓ 👔 Dev Lead Review
- ✓ ⚡ Streaming

**Input:**
```
What is Python?
```

**Expected Output:**

```
⚙️ Status: 🔍 Analyzing requirements...
⚙️ Status: 📋 Creating action plan...
⚙️ Status: ⚙️ Executing Developer Agent...

🤖 Assistant
Python is a high-level programming language...

⚙️ Status: 👔 Dev Lead reviewing changes...

👔 Dev Lead Review
Decision: APPROVED
Summary: Answer is accurate and helpful
```

✅ **Pass if:** Dev Lead reviews even though no tools were used

---

### Test 4: Review Disabled ✅

**Setup:**
- ✓ Show Thought Process
- ✗ 👔 Dev Lead Review (DISABLED)
- ✓ ⚡ Streaming

**Input:**
```
Create a Python file
```

**Expected Output:**

```
⚙️ Status: 🔍 Analyzing requirements...
⚙️ Status: 📋 Creating action plan...
⚙️ Status: ⚙️ Executing Developer Agent...
⚙️ Status: Step 1: write_file - ...

🤖 Assistant
File created successfully
```

✅ **Pass if:** No Dev Lead review appears

---

### Test 5: Multiple Steps ✅

**Setup:**
- ✓ Show Thought Process
- ✓ 👔 Dev Lead Review
- ✓ ⚡ Streaming

**Input:**
```
Create a Python file with a calculator class that has add and subtract methods
```

**Expected Output:**

```
⚙️ Status: 🔍 Analyzing requirements...
⚙️ Status: 📋 Creating action plan...
⚙️ Status: ⚙️ Executing Developer Agent...
⚙️ Status: Step 1: write_file - {"file_path": "calculator.py", "content": "class Calculator:\n    def add...
⚙️ Status: Step 2: read_file - calculator.py

🤖 Assistant
Created calculator.py with Calculator class including add and subtract methods.

👔 Dev Lead Review
Decision: APPROVED
Comments:
- Class structure is well-organized
- Methods are properly defined
- Good use of docstrings
```

✅ **Pass if:** Multiple steps shown, review appears

---

### Test 6: Error Handling ✅

**Setup:**
- ✓ Show Thought Process
- ✓ 👔 Dev Lead Review
- ✓ ⚡ Streaming

**Input:**
```
Delete a file that doesn't exist
```

**Expected Output:**

```
⚙️ Status: 🔍 Analyzing requirements...
⚙️ Status: 📋 Creating action plan...
⚙️ Status: ⚙️ Executing Developer Agent...
⚙️ Status: Step 1: delete_file - nonexistent.txt

🤖 Assistant
Error: File not found

👔 Dev Lead Review
Decision: NEEDS_IMPROVEMENT
Issues:
- File doesn't exist
Suggestions:
- Check if file exists before attempting deletion
```

✅ **Pass if:** Error handled gracefully, Dev Lead reviews the error

---

## Troubleshooting

### Issue: No Status Messages

**Symptoms:**
- Only final result shows
- No "Analyzing requirements..." messages

**Check:**
1. Is ⚡ Streaming enabled?
2. Check browser console for errors
3. Check backend logs

**Fix:**
```bash
# Restart both backend and frontend
# Clear browser cache
```

---

### Issue: Dev Lead Not Appearing

**Symptoms:**
- Developer result shows
- No review appears

**Check:**
1. Is 👔 Dev Lead Review enabled?
2. Check backend logs for errors
3. Check if `dev_lead_agent` initialized

**Fix:**
```bash
# Check backend logs:
tail -f logs/uvicorn.log

# Should see:
# "Dev Lead reviewing changes..."
```

---

### Issue: Status Messages Don't Update

**Symptoms:**
- Multiple status messages stack up
- Don't replace each other

**Check:**
1. UI code filtering status messages correctly
2. Browser console for errors

**Fix:**
- Refresh page
- Check `App.tsx` line 144: `filter((m: Message) => m.role !== 'status')`

---

### Issue: Long Pause Before Results

**Symptoms:**
- Status messages appear
- Long wait
- Then results appear quickly

**This is EXPECTED:**
- Agent execution is synchronous
- Must complete before streaming results
- This is a limitation of LangChain's AgentExecutor

**Not a bug!**

---

## API Testing

### Test Streaming Endpoint

```bash
curl -N -X POST http://localhost:8000/query/stream \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create a Python file",
    "show_details": true,
    "enable_review": true
  }'
```

**Expected:** NDJSON stream
```json
{"type":"status","message":"🔍 Analyzing requirements..."}
{"type":"status","message":"📋 Creating action plan..."}
{"type":"status","message":"⚙️ Executing Developer Agent..."}
{"type":"step","step_number":1,"action":"write_file","action_input":"...","observation":"..."}
{"type":"developer_result","response":"File created","thought_process":[...]}
{"type":"status","message":"👔 Dev Lead reviewing changes..."}
{"type":"review","review":{"status":"success","decision":"approved",...}}
{"type":"complete","message":"✅ Task completed"}
```

---

### Test Traditional Endpoint

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

**Expected:** JSON response
```json
{
  "status": "success",
  "response": "File created",
  "thought_process": [...],
  "review": {
    "status": "success",
    "decision": "approved",
    "review": "Code meets requirements",
    "comments": ["Good structure"],
    "issues": [],
    "suggestions": []
  }
}
```

---

## Success Criteria

### ✅ All Tests Pass If:

1. **Status messages appear and update** (not stack)
2. **Steps shown after agent completes**
3. **Developer result displays correctly**
4. **Dev Lead review ALWAYS appears** (when enabled)
5. **Review shows decision, summary, comments**
6. **No errors in console or backend logs**
7. **Final state is clean** (no status messages left)

---

## Performance Notes

### Expected Timing

- **Status messages:** Instant (< 0.5s)
- **Agent execution:** 2-10s (depends on task)
- **Step streaming:** Fast (< 1s)
- **Dev Lead review:** 1-3s
- **Total:** 3-15s per request

### If Slower:

- Check GCP Vertex AI latency
- Check network connection
- Check backend CPU usage

---

## Summary

✅ **Streaming works** - Shows progress updates  
✅ **Steps displayed** - See what agent did  
✅ **Dev Lead triggered** - Reviews every response  
✅ **Clean UI** - Status messages update properly  
✅ **Error handling** - Graceful failures  

**The system is ready for testing!** 🚀

Run through all 6 test cases to verify everything works correctly.
