# Append vs Write Fix - Complete Solution

## Issue

Agent was incorrectly using `append_to_file` for Python files, causing:
- **Deleted most of the content** when trying to modify existing code
- **Added JSON instead of Python code** to files
- **Broke file structure** by not understanding append vs write

## Root Cause

The agent didn't understand the difference between:
- **`write_file`** - REPLACES entire file content
- **`append_to_file`** - ADDS to the end of file

The prompt didn't clearly explain:
1. When to use `write_file` vs `append_to_file`
2. That modifying existing code requires `write_file` with COMPLETE content
3. That `append_to_file` should only be used for adding NEW functions

## Complete Solution

### 1. **Clear Workflow in Prompt**

```
CRITICAL WORKFLOW FOR UPDATING PYTHON FILES:
1. ALWAYS read the file first with read_file to see current content
2. Understand the existing code structure
3. For modifications: Use write_file with the COMPLETE updated file content
4. For adding new functions: Use append_to_file with ONLY the new code to add
```

### 2. **Updated Tool Descriptions**

**write_file:**
```
Creates a new file or REPLACES entire file content. 
Use for: (1) Creating new files, (2) Modifying existing code. 
When modifying, provide the COMPLETE file content with your changes.
```

**append_to_file:**
```
Adds content to the END of an existing file. 
Use ONLY for adding NEW functions/classes to Python files. 
Do NOT use for modifying existing code. 
Always start content with \n\n for proper spacing.
```

### 3. **Concrete Examples in Prompt**

**EXAMPLE 1 - Creating a new file:**
```
Action: write_file
Action Input: {"file_path": "hello.py", "content": "def hello():\n    '''Say hello'''\n    print('Hello, World!')\n"}
```

**EXAMPLE 2 - Adding a function to existing file:**
```
Step 1: Read existing file
Action: read_file
Action Input: hello.py
Observation: def hello():\n    print('Hello')\n

Step 2: Append new function (note the \n\n at start for spacing)
Action: append_to_file
Action Input: {"file_path": "hello.py", "content": "\n\ndef goodbye():\n    '''Say goodbye'''\n    print('Goodbye!')\n"}
```

**EXAMPLE 3 - Modifying existing function:**
```
Step 1: Read file
Action: read_file
Action Input: calc.py
Observation: def add(a, b):\n    return a + b\n

Step 2: Write COMPLETE file with modification
Action: write_file
Action Input: {"file_path": "calc.py", "content": "def add(a, b):\n    '''Add two numbers'''\n    return a + b\n"}
```

---

## How It Works

### Scenario 1: Creating a New File

**User:** "Create a file hello.py with a hello function"

**Agent:**
```
Action: write_file
Action Input: {"file_path": "hello.py", "content": "def hello():\n    print('Hello')\n"}
```

**Result:**
```python
def hello():
    print('Hello')
```

✅ **Correct!**

---

### Scenario 2: Adding a New Function

**User:** "Add a goodbye function to hello.py"

**Agent Step 1:**
```
Action: read_file
Action Input: hello.py
Observation: {"status": "success", "content": "def hello():\n    print('Hello')\n"}
```

**Agent Step 2:**
```
Action: append_to_file
Action Input: {"file_path": "hello.py", "content": "\n\ndef goodbye():\n    print('Goodbye')\n"}
```

**Result:**
```python
def hello():
    print('Hello')

def goodbye():
    print('Goodbye')
```

✅ **Correct!** New function added at the end.

---

### Scenario 3: Modifying Existing Function

**User:** "Update the hello function to print Hello World"

**Agent Step 1:**
```
Action: read_file
Action Input: hello.py
Observation: {"status": "success", "content": "def hello():\n    print('Hello')\n"}
```

**Agent Step 2:**
```
Action: write_file
Action Input: {"file_path": "hello.py", "content": "def hello():\n    print('Hello World')\n"}
```

**Result:**
```python
def hello():
    print('Hello World')
```

✅ **Correct!** Entire file replaced with updated content.

---

## What Was Wrong Before

### ❌ Wrong Approach 1: Using append_to_file to Modify

**User:** "Update hello function to print Hello World"

**Agent (WRONG):**
```
Action: append_to_file
Action Input: {"file_path": "hello.py", "content": "def hello():\n    print('Hello World')\n"}
```

**Result:**
```python
def hello():
    print('Hello')
def hello():
    print('Hello World')
```

❌ **Wrong!** Now there are two `hello` functions, and the file is broken.

---

### ❌ Wrong Approach 2: Using write_file with Only New Code

**User:** "Add a goodbye function"

**Agent (WRONG):**
```
Action: write_file
Action Input: {"file_path": "hello.py", "content": "def goodbye():\n    print('Goodbye')\n"}
```

**Result:**
```python
def goodbye():
    print('Goodbye')
```

❌ **Wrong!** The original `hello` function is gone!

---

## Decision Tree for Agent

```
User wants to modify Python file
            |
            v
    Read file first
            |
            v
    What type of change?
            |
    +-------+-------+
    |               |
    v               v
MODIFY          ADD NEW
existing        function/class
code            |
|               v
v           Use append_to_file
Use write_file  with ONLY new code
with COMPLETE   (start with \n\n)
file content
```

---

## Critical Rules

### ✅ DO:

1. **Always read file first** before modifying
2. **Use write_file** when:
   - Creating new files
   - Modifying existing functions
   - Changing existing code
   - Updating docstrings
   - Fixing bugs in existing code

3. **Use append_to_file** when:
   - Adding NEW functions to end of file
   - Adding NEW classes to end of file
   - Start content with `\n\n` for spacing

4. **Provide complete content** when using write_file
5. **Use single quotes** for Python strings
6. **Use triple single quotes** for docstrings

### ❌ DON'T:

1. **Don't use append_to_file** to modify existing code
2. **Don't use write_file** with only partial content
3. **Don't forget** to read file before modifying
4. **Don't add** JSON objects to Python files
5. **Don't escape** quotes in Python code

---

## Files Changed

1. **agent/developer_agent.py**
   - Lines 294-296: Updated `write_file` tool description
   - Lines 299-301: Updated `append_to_file` tool description
   - Lines 349-395: Completely rewrote prompt with clear workflow and examples

---

## Testing

### Test 1: Add Function to Existing File

```bash
# Create initial file
echo "def hello():\n    print('Hello')" > test.py

# Ask agent to add function
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Add a goodbye function to test.py"}'

# Verify
cat test.py
```

**Expected:**
```python
def hello():
    print('Hello')

def goodbye():
    print('Goodbye')
```

**Should NOT be:**
```python
def goodbye():
    print('Goodbye')
```
(Original function missing)

---

### Test 2: Modify Existing Function

```bash
# Create initial file
echo "def add(a, b):\n    return a + b" > calc.py

# Ask agent to add docstring
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Add a docstring to the add function in calc.py"}'

# Verify
cat calc.py
```

**Expected:**
```python
def add(a, b):
    '''Add two numbers'''
    return a + b
```

**Should NOT be:**
```python
def add(a, b):
    return a + b
def add(a, b):
    '''Add two numbers'''
    return a + b
```
(Duplicate function)

---

### Test 3: Create New File

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a file greet.py with a greet function"}'

# Verify
cat greet.py
```

**Expected:**
```python
def greet(name):
    print(f'Hello, {name}!')
```

---

## Summary

✅ **Clear workflow** - Read → Decide → Write/Append  
✅ **Updated tool descriptions** - Explains when to use each  
✅ **Concrete examples** - Shows correct usage patterns  
✅ **Decision tree** - Agent knows which tool to use  
✅ **Critical rules** - Explicit do's and don'ts  

### Key Principle:

**Modifying existing code = write_file with COMPLETE content**  
**Adding new code = append_to_file with ONLY new code**

---

## How to Apply

### 1. Restart Server
```bash
uvicorn main:app --reload
```

### 2. Test Adding Function
```bash
# Create test file
echo "def hello():\n    print('Hello')" > test.py

# Ask agent to add function
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Add a goodbye function to test.py"}'

# Verify both functions exist
cat test.py
```

### 3. Test Modifying Function
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Update hello function in test.py to print Hello World"}'

# Verify modification worked and goodbye function still exists
cat test.py
```

---

**The agent now correctly handles append vs write for Python files!** 🎉
