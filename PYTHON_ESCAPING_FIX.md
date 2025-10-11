# Python Code Escaping Fix - Complete Solution

## Issue

Agent was adding unnecessary escape characters to Python code when updating files:
- `"""docstring"""` → `\"\"\"docstring\"\"\"`  ❌
- `print("hello")` → `print(\"hello\")`  ❌
- `raise ValueError(f"msg")` → `raise ValueError(f\"msg\")`  ❌

This breaks Python syntax and makes files unusable.

## Root Causes

### 1. **Double Processing of Escape Sequences**

The code was doing unnecessary normalization:
```python
# Line 196 (OLD)
content = content.replace("\\n", "\n").replace("\\t", "\t")
```

**Problem:** JSON parser already converts `\\n` → newline. The extra replacement was causing issues when agent added extra escaping.

### 2. **Unclear Prompt Instructions**

The prompt said "use single quotes" but didn't show WRONG examples, so the agent sometimes:
- Escaped double quotes: `print(\"hello\")`
- Escaped docstrings: `\\\"\\\"\\\"docstring\\\"\\\"\\\"`
- Added extra backslashes

## Complete Solution

### Fix 1: Remove Unnecessary Content Processing

**Before:**
```python
content = content.replace("\\n", "\n").replace("\\t", "\t")
return self.file_ops.write_file(file_path, content)
```

**After:**
```python
# Content is already properly decoded by JSON parser
# No additional processing needed
return self.file_ops.write_file(file_path, content)
```

**Why:** `json.loads()` automatically handles all escape sequences. When the agent sends:
```json
{"content": "def hello():\n    print('hi')"}
```

The JSON parser converts `\n` to actual newlines. No further processing needed!

---

### Fix 2: Updated Prompt with WRONG Examples

**Added to prompt:**
```
PYTHON CODE RULES:
1. Use \n for newlines in the JSON string
2. Use SINGLE quotes ' for Python strings (NOT double quotes ")
3. Use TRIPLE SINGLE quotes ''' for Python docstrings
4. NEVER add backslashes before quotes in Python code
5. Write Python code naturally, the JSON parser handles everything

WRONG EXAMPLES (DO NOT DO THIS):
❌ {"file_path": "test.py", "content": "print(\"hello\")"}  // WRONG: Do not escape Python quotes
❌ {"file_path": "doc.py", "content": "\"\"\"docstring\"\"\""}  // WRONG: Do not escape docstrings
✅ {"file_path": "test.py", "content": "print('hello')"}  // CORRECT: Use single quotes
✅ {"file_path": "doc.py", "content": "'''docstring'''"}  // CORRECT: Use triple single quotes
```

**Why:** Showing WRONG examples helps the LLM understand what NOT to do.

---

### Fix 3: Fixed Import Typo

**Before:**
```python
from langchin_core.prompt_value import StringPromptValue, PromptValue
```

**After:**
```python
from langchain_core.prompt_values import StringPromptValue
from langchain_core.prompt_values import PromptValue
```

---

## How JSON Parsing Works

### Understanding the Flow:

```
Agent sends JSON:
{"file_path": "test.py", "content": "def hello():\n    print('hi')"}
                                                    ↓
JSON parser (json.loads):
{"file_path": "test.py", "content": "def hello():\n    print('hi')"}
                                     (actual newline here)
                                                    ↓
File written:
def hello():
    print('hi')
```

### What Happens with Extra Escaping:

```
Agent sends (WRONG):
{"file_path": "test.py", "content": "print(\\"hello\\")"}
                                                    ↓
JSON parser:
{"file_path": "test.py", "content": "print(\"hello\")"}
                                     (literal backslash-quote)
                                                    ↓
File written (BROKEN):
print(\"hello\")  // Invalid Python!
```

---

## Correct Examples for All Cases

### Example 1: Simple Function
```json
{"file_path": "hello.py", "content": "def hello():\n    print('Hello, World!')\n"}
```
**Result:**
```python
def hello():
    print('Hello, World!')
```

---

### Example 2: Function with Docstring
```json
{"file_path": "add.py", "content": "def add(a, b):\n    '''Add two numbers'''\n    return a + b\n"}
```
**Result:**
```python
def add(a, b):
    '''Add two numbers'''
    return a + b
```

---

### Example 3: Function with F-String
```json
{"file_path": "greet.py", "content": "def greet(name):\n    return f'Hello, {name}!'\n"}
```
**Result:**
```python
def greet(name):
    return f'Hello, {name}!'
```

---

### Example 4: Function with Exception
```json
{"file_path": "check.py", "content": "def check(x):\n    if x < 0:\n        raise ValueError(f'Value must be positive: {x}')\n"}
```
**Result:**
```python
def check(x):
    if x < 0:
        raise ValueError(f'Value must be positive: {x}')
```

---

### Example 5: Multi-line Docstring
```json
{"file_path": "calc.py", "content": "def calculate(x, y):\n    '''\n    Calculate something.\n    \n    Args:\n        x: First number\n        y: Second number\n    '''\n    return x + y\n"}
```
**Result:**
```python
def calculate(x, y):
    '''
    Calculate something.
    
    Args:
        x: First number
        y: Second number
    '''
    return x + y
```

---

### Example 6: Class with Methods
```json
{"file_path": "person.py", "content": "class Person:\n    '''Represents a person'''\n    \n    def __init__(self, name):\n        self.name = name\n    \n    def greet(self):\n        return f'Hi, I am {self.name}'\n"}
```
**Result:**
```python
class Person:
    '''Represents a person'''
    
    def __init__(self, name):
        self.name = name
    
    def greet(self):
        return f'Hi, I am {self.name}'
```

---

## Key Principles

### 1. JSON Parser Handles Everything
- Agent sends: `"content": "print('hi')"`
- JSON parser receives: `print('hi')` (no escaping in Python code)
- File gets: `print('hi')` ✓

### 2. Use Single Quotes in Python Code
- ✅ `print('hello')`
- ❌ `print("hello")` (requires escaping in JSON)

### 3. Use Triple Single Quotes for Docstrings
- ✅ `'''docstring'''`
- ❌ `"""docstring"""` (requires escaping in JSON)

### 4. Never Add Extra Backslashes
- ✅ `f'value: {x}'`
- ❌ `f\'value: {x}\'` (breaks Python)

### 5. Only Escape Newlines
- ✅ `"def hello():\n    pass"`
- ❌ `"def hello():\n    pass"` (actual newline breaks JSON)

---

## Files Changed

1. **agent/developer_agent.py**
   - Lines 7-9: Fixed imports (langchain_core)
   - Lines 195-197: Removed unnecessary content processing in `_write_file_wrapper`
   - Lines 252-254: Removed unnecessary content processing in `_append_to_file_wrapper`
   - Lines 349-373: Updated prompt with PYTHON CODE RULES and WRONG examples

---

## Testing

### Test 1: Function with Docstring
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a function add(a,b) with a docstring that says Add two numbers"}'

# Verify
cat <filename>.py
```

**Expected:**
```python
def add(a, b):
    '''Add two numbers'''
    return a + b
```

**NOT:**
```python
def add(a, b):
    \"\"\"Add two numbers\"\"\"  # WRONG!
    return a + b
```

---

### Test 2: Function with F-String
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a greet function that uses f-string to greet a person by name"}'

# Verify
cat <filename>.py
```

**Expected:**
```python
def greet(name):
    return f'Hello, {name}!'
```

**NOT:**
```python
def greet(name):
    return f\"Hello, {name}!\"  # WRONG!
```

---

### Test 3: Exception with Message
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Create a function that raises ValueError with a message"}'

# Verify
cat <filename>.py
```

**Expected:**
```python
def check(value):
    if value < 0:
        raise ValueError(f'Value must be positive')
```

**NOT:**
```python
def check(value):
    if value < 0:
        raise ValueError(f\'Value must be positive\')  # WRONG!
```

---

## Summary of Changes

✅ **Removed content normalization** - JSON parser handles everything  
✅ **Updated prompt with PYTHON CODE RULES** - Clear guidelines  
✅ **Added WRONG examples** - Shows what NOT to do  
✅ **Fixed imports** - Corrected langchain_core typo  
✅ **Emphasized single quotes** - Avoids escaping issues  
✅ **Emphasized triple single quotes** - For docstrings  

---

## How to Apply

### 1. Restart Server
```bash
uvicorn main:app --reload
```

### 2. Create New Session
```bash
SESSION_ID=$(curl -X POST http://localhost:8000/session/create | jq -r '.session_id')
```

### 3. Test with Docstring
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"Create a function with a docstring\", \"session_id\": \"$SESSION_ID\"}"
```

### 4. Verify File
```bash
cat <filename>.py
# Should have '''docstring''' NOT \"\"\"docstring\"\"\"
```

---

## Expected Behavior

### Before Fix:
```python
# Agent creates:
def hello():
    \"\"\"Say hello\"\"\"  # BROKEN!
    print(\"Hello\")  # BROKEN!
```

### After Fix:
```python
# Agent creates:
def hello():
    '''Say hello'''  # CORRECT!
    print('Hello')  # CORRECT!
```

---

**Python files are now created with correct syntax, no extra escaping!** 🎉

## Documentation

- **This Guide:** `PYTHON_ESCAPING_FIX.md`
- **Format Guide:** `PYTHON_CODE_FORMAT_GUIDE.md`
- **All Fixes:** `ALL_FIXES_SUMMARY.md`
