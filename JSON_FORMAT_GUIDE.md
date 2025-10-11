# JSON Format Guide for Agent

## Common Issue: Invalid JSON Input Error

### Error Message
```
{'status': 'error', 'message': 'Invalid JSON format. Error: ...'}
```

### Root Cause
The agent is not formatting the JSON input correctly for `write_file` and `append_to_file` tools.

## Correct JSON Format

### For write_file

**Correct:**
```json
{"file_path": "test.py", "content": "def hello():\n    print('Hello')"}
```

**Incorrect Examples:**
```
❌ {file_path: "test.py", content: "..."}  // Missing quotes around keys
❌ {'file_path': 'test.py', 'content': '...'}  // Single quotes (not valid JSON)
❌ {"file_path": "test.py" "content": "..."}  // Missing comma
❌ {
    "file_path": "test.py",
    "content": "..."
   }  // Multi-line (agent should use single line)
```

### For append_to_file

**Correct:**
```json
{"file_path": "test.py", "content": "\ndef goodbye():\n    print('Bye')"}
```

## How the Agent Should Use It

### Example 1: Create a Python File

```
Action: write_file
Action Input: {"file_path": "calculator.py", "content": "def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b"}
```

### Example 2: Append to a File

```
Action: append_to_file
Action Input: {"file_path": "calculator.py", "content": "\ndef multiply(a, b):\n    return a * b"}
```

### Example 3: File with Special Characters

```
Action: write_file
Action Input: {"file_path": "config.json", "content": "{\"database\": \"localhost\", \"port\": 5432}"}
```

Note: Quotes inside the content must be escaped with backslash.

## What We've Done to Fix This

### 1. Enhanced Error Messages

The error messages now include:
- The specific JSON parsing error
- A concrete example of correct format
- Reminder to escape quotes

### 2. Updated Tool Descriptions

Tool descriptions now explicitly state:
- "Input MUST be valid JSON on ONE LINE"
- Include examples in the description

### 3. Added Examples to Prompt

The agent prompt now includes:
- Clear JSON format section
- Multiple examples
- Emphasis on single-line format

### 4. Better Error Feedback

When JSON parsing fails, the agent receives:
```
Invalid JSON format. Error: Expecting property name enclosed in double quotes: line 1 column 2 (char 1). 
You MUST use valid JSON like this example: {"file_path": "example.py", "content": "print('hello')"}. 
Make sure to escape quotes in the content.
```

## Testing the Fix

### Test 1: Simple File Creation

**Request:**
```
Create a file called hello.py with a function that prints "Hello, World!"
```

**Expected Agent Action:**
```
Action: write_file
Action Input: {"file_path": "hello.py", "content": "def hello():\n    print('Hello, World!')"}
```

### Test 2: File with Multiple Functions

**Request:**
```
Create a calculator.py with add and subtract functions
```

**Expected Agent Action:**
```
Action: write_file
Action Input: {"file_path": "calculator.py", "content": "def add(a, b):\n    return a + b\n\ndef subtract(a, b):\n    return a - b"}
```

### Test 3: Append to Existing File

**Request:**
```
Add a multiply function to calculator.py
```

**Expected Agent Action:**
```
Action: append_to_file
Action Input: {"file_path": "calculator.py", "content": "\ndef multiply(a, b):\n    return a * b"}
```

## If Agent Still Fails

### Check 1: Restart the Server

The agent needs to reload with the new prompt:
```bash
# Stop server (Ctrl+C)
uvicorn main:app --reload
```

### Check 2: Clear Session

Create a new session to ensure clean state:
```bash
curl -X POST http://localhost:8000/session/create
```

### Check 3: Be Specific in Requests

Instead of:
```
❌ "Can you help me create a file?"
❌ "What would you put in a calculator file?"
```

Use:
```
✅ "Create a file called calculator.py with add and subtract functions"
✅ "Write a hello.py file with a hello function"
```

### Check 4: Review Agent Logs

Look for the JSON that the agent is trying to use:
```
Action Input: {whatever the agent sent}
```

If it's malformed, the error message will guide the agent to fix it.

## Why This Happens

### LLM Behavior

Language models sometimes:
1. Use single quotes instead of double quotes
2. Forget to escape quotes in content
3. Try to format JSON across multiple lines
4. Omit quotes around keys

### Our Solution

We've added:
1. **Explicit examples** in the prompt
2. **Clear error messages** that teach the correct format
3. **Tool descriptions** that emphasize the format
4. **Format section** in the prompt with examples

## Expected Behavior After Fix

### Before Fix:
```
Agent tries: {file_path: "test.py", content: "..."}
Error: Invalid JSON
Agent tries: {'file_path': 'test.py', 'content': '...'}
Error: Invalid JSON
Agent tries again... fails multiple times
```

### After Fix:
```
Agent sees examples in prompt
Agent uses: {"file_path": "test.py", "content": "..."}
Success! ✓
```

## Monitoring

### Check Agent's Learning

After the fix, the agent should:
1. ✅ Use correct JSON format on first try
2. ✅ Properly escape quotes in content
3. ✅ Use single-line JSON
4. ✅ Include both required fields

### If Still Failing

The error message will show exactly what the agent sent:
```
Invalid JSON format. Error: <specific error>
You MUST use valid JSON like this example: {"file_path": "example.py", "content": "print('hello')"}
```

This feedback loop helps the agent learn the correct format.

## Summary

✅ **Enhanced error messages** with examples  
✅ **Updated tool descriptions** with format emphasis  
✅ **Added JSON format section** to prompt  
✅ **Included concrete examples** in prompt  
✅ **Better error feedback** to guide agent  

The agent should now correctly format JSON inputs for file operations!
