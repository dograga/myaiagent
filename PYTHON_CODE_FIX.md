# Python Code Writing Fix

## Issue

Agent was failing to write Python code with error:
```
{'status': 'error', 'message': 'Invalid JSON format. Error: Unterminated string starting at: line 1 column 41 (char 40)...'}
```

The agent was having trouble with:
- Escaping quotes in Python strings
- Properly formatting newlines
- Handling Python code with `print()` statements

## Root Cause

When writing Python code like:
```python
print("Hello")
```

The agent was trying to create JSON like:
```json
{"file_path": "test.py", "content": "print("hello")"}
```

This breaks JSON because the quotes inside `print()` terminate the JSON string prematurely.

## Solution Implemented

### 1. **Fallback Parser**

Added regex-based fallback parser that:
- Extracts `file_path` and `content` even if JSON is malformed
- Automatically unescapes common patterns
- Handles edge cases gracefully

```python
try:
    # Try JSON first
    data = json.loads(input_str)
except json.JSONDecodeError:
    # Fallback: extract with regex
    file_path_match = re.search(r'["\'']file_path["\']\s*:\s*["\'']([^"\'\\\/]+)["\'']', input_str)
    content_match = re.search(r'["\'']content["\']\s*:\s*["\''](.+)["\']\s*}\s*$', input_str, re.DOTALL)
    
    if file_path_match and content_match:
        content = content_match.group(1)
        # Unescape patterns
        content = content.replace('\\n', '\n').replace('\\t', '\t')
        content = content.replace('\\"', '"').replace("\\'", "'")
        # Use the content!
```

### 2. **Updated Prompt with Clear Examples**

**Before:**
```
Action Input: {"file_path": "test.py", "content": "def hello():\n    print('Hello')"}
```

**After:**
```
Action Input: {"file_path": "test.py", "content": "def hello():\\n    print('Hello, World!')\\n"}
```

Key changes:
- Shows `\\n` explicitly (not actual newlines)
- Emphasizes using SINGLE quotes in Python code
- Multiple examples including Python functions

### 3. **Added KEY RULES Section**

```
KEY RULES:
- Use \\n for line breaks (NOT actual newlines)
- Use single quotes ' inside Python code (NOT double quotes ")
- Keep JSON on ONE line
- Example: print('hello') NOT print(\"hello\")
```

This explicitly tells the agent:
- ✅ Use `print('hello')` 
- ❌ Don't use `print("hello")`

## How It Works

### Example 1: Simple Python Function

**Request:**
```
Create a file hello.py with a function that prints "Hello, World!"
```

**Agent Should Use:**
```
Action: write_file
Action Input: {"file_path": "hello.py", "content": "def hello():\\n    print('Hello, World!')\\n"}
```

**Result:**
```python
def hello():
    print('Hello, World!')
```

### Example 2: Multiple Functions

**Request:**
```
Create calculator.py with add and subtract functions
```

**Agent Should Use:**
```
Action: write_file
Action Input: {"file_path": "calculator.py", "content": "def add(a, b):\\n    return a + b\\n\\ndef subtract(a, b):\\n    return a - b\\n"}
```

**Result:**
```python
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
```

### Example 3: Code with Strings

**Request:**
```
Create a greeting function that prints a message
```

**Agent Should Use:**
```
Action: write_file
Action Input: {"file_path": "greet.py", "content": "def greet(name):\\n    print('Hello, ' + name + '!')\\n"}
```

**Result:**
```python
def greet(name):
    print('Hello, ' + name + '!')
```

Note: Uses single quotes, no escaping needed!

## Files Changed

1. **agent/developer_agent.py**
   - Lines 148-172: Added fallback parser to `_write_file_wrapper()`
   - Lines 186-207: Added fallback parser to `_append_to_file_wrapper()`
   - Lines 271-290: Updated AUTO-APPROVE prompt with clear examples
   - Lines 322-341: Updated APPROVAL prompt with clear examples

## Testing

### Test Case 1: Simple Print Statement

**Request:**
```
Create a file test.py with a hello function that prints "Hello"
```

**Expected Action:**
```
Action: write_file
Action Input: {"file_path": "test.py", "content": "def hello():\\n    print('Hello')\\n"}
```

**Expected File:**
```python
def hello():
    print('Hello')
```

### Test Case 2: Multiple Functions

**Request:**
```
Create calculator.py with add, subtract, multiply functions
```

**Expected Action:**
```
Action: write_file
Action Input: {"file_path": "calculator.py", "content": "def add(a, b):\\n    return a + b\\n\\ndef subtract(a, b):\\n    return a - b\\n\\ndef multiply(a, b):\\n    return a * b\\n"}
```

**Expected File:**
```python
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b
```

### Test Case 3: Code with Complex Strings

**Request:**
```
Create a function that prints a formatted message
```

**Expected Action:**
```
Action: write_file
Action Input: {"file_path": "message.py", "content": "def show_message(name, age):\\n    print('Name: ' + name + ', Age: ' + str(age))\\n"}
```

**Expected File:**
```python
def show_message(name, age):
    print('Name: ' + name + ', Age: ' + str(age))
```

## How to Apply

### 1. Restart the Server

```bash
# Stop current server (Ctrl+C)
uvicorn main:app --reload
```

### 2. Create New Session

In UI: Click "New Session"

Or via API:
```bash
curl -X POST http://localhost:8000/session/create
```

### 3. Test with Python Code

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Create a file hello.py with a function that prints Hello World",
    "session_id": "YOUR_SESSION_ID"
  }'
```

### 4. Verify the File

```bash
cat hello.py
```

Should show:
```python
def hello():
    print('Hello World')
```

## Expected Behavior

### Before Fix:
```
Agent tries: {"file_path": "test.py", "content": "print("hello")"}
Error: Unterminated string
Agent retries with same error
Fails multiple times
```

### After Fix:
```
Agent sees examples with single quotes
Agent uses: {"file_path": "test.py", "content": "print('hello')"}
Success! ✓

OR if agent still makes mistake:
Fallback parser extracts content anyway
Success! ✓
```

## Key Improvements

### 1. **Explicit Examples**
- Shows `\\n` for newlines
- Shows single quotes in Python code
- Multiple realistic examples

### 2. **Fallback Parser**
- Handles malformed JSON gracefully
- Extracts content even with escaping issues
- Automatically unescapes common patterns

### 3. **Clear Rules**
- "Use single quotes ' NOT double quotes \""
- "Use \\n for line breaks"
- "Keep JSON on ONE line"

## Why Single Quotes?

**Double quotes require escaping:**
```json
{"content": "print(\"hello\")"}  // Complex!
```

**Single quotes don't:**
```json
{"content": "print('hello')"}  // Simple!
```

The agent finds it easier to use single quotes, avoiding the need to escape quotes in Python strings.

## Troubleshooting

### If Still Getting Errors

1. **Check the actual JSON the agent sent:**
   Look at the error message or logs

2. **Verify server restarted:**
   ```bash
   # Should see "Application startup complete"
   ```

3. **Create new session:**
   Old sessions may have cached bad patterns

4. **Be specific in requests:**
   ```
   ✅ "Create hello.py with a hello function"
   ❌ "Can you help with Python?"
   ```

### If Fallback Parser Activates

The fallback parser will try to extract content even if JSON is malformed. Check logs for:
```
# If you see this, fallback worked
File written successfully
```

## Summary

✅ **Added fallback parser** for malformed JSON  
✅ **Updated prompts** with clear Python examples  
✅ **Emphasized single quotes** to avoid escaping  
✅ **Added KEY RULES** section for clarity  
✅ **Better error messages** with correct examples  

**Result:** Agent can now write Python code reliably, using single quotes to avoid JSON escaping issues!

## Documentation

- **This Guide:** `PYTHON_CODE_FIX.md`
- **JSON Guide:** `JSON_FORMAT_GUIDE.md`
- **Troubleshooting:** `TROUBLESHOOTING.md`

---

**The agent now handles Python code correctly with single quotes and proper newline formatting!** 🎉
