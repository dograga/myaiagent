# Escaping Existing Code Fix

## Issues

1. **Escaping existing quotes:** `"""Get approval summary"""` → `\"\"\"Get approval summary\"\"\"`
2. **Escaping dictionary keys:** `"approvalcount": group_data` → `\"approvalcount\": group_data`
3. **Removing code:** Some modules at the bottom were removed without reason

## Root Cause

When the agent reads a file with double quotes (`"`) or triple double quotes (`"""`), and then tries to write it back using `write_file`, the LLM is:
1. Adding backslashes to escape the quotes
2. Not including all the original content

This happens because:
- The LLM doesn't understand it should use SINGLE quotes in the output
- The LLM thinks it needs to escape existing double quotes for JSON
- The LLM might be truncating long files

## Solution

Added explicit instructions to the prompt about handling existing code.

### New Section in Prompt

```
⚠️ CRITICAL - WHEN MODIFYING EXISTING FILES:
When you read a file and need to modify it, you MUST:
1. Include ALL existing code (don't remove any functions/classes)
2. Use SINGLE quotes ' for Python strings (NOT double quotes ")
3. If existing code has triple quotes """, convert to ''' in your output
4. DO NOT add backslashes before existing quotes
5. Keep all imports, all functions, all classes - just add your changes

Example - If file has:
def get_data():
    """Get data from API"""
    return data

When modifying, write:
{"file_path": "file.py", "content": "def get_data():\n    '''Get data from API'''\n    return data\n"}

Notice: """ became ''' (triple single quotes)
```

---

## How It Should Work

### Scenario: Modify File with Docstrings

**Step 1: Agent Reads File**
```
Action: read_file
Action Input: api.py
```

**Observation:**
```python
def get_approval_summary():
    """Get approval summary from database"""
    data = {"approvalcount": group_data}
    return data
```

**Step 2: Agent Modifies (Correct)**
```
Action: write_file
Action Input: {"file_path": "api.py", "content": "def get_approval_summary():\n    '''Get approval summary from database'''\n    data = {'approvalcount': group_data}\n    return data\n"}
```

**Notice:**
- `"""` → `'''` (triple single quotes)
- `"approvalcount"` → `'approvalcount'` (single quotes)
- No backslashes added
- All content preserved

**Result:**
```python
def get_approval_summary():
    '''Get approval summary from database'''
    data = {'approvalcount': group_data}
    return data
```

✅ **Correct!**

---

## What Was Wrong Before

### Before: Escaping Quotes

**Agent tried:**
```
Action: write_file
Action Input: {"file_path": "api.py", "content": "def get_approval_summary():\n    \"\"\"Get approval summary\"\"\"\n    data = {\"approvalcount\": group_data}\n"}
```

**Problem:** LLM added backslashes to escape the quotes

**Result in file:**
```python
def get_approval_summary():
    \"\"\"Get approval summary\"\"\"
    data = {\"approvalcount\": group_data}
```

❌ **Wrong!** Backslashes break Python syntax.

---

### After: Using Single Quotes

**Agent does:**
```
Action: write_file
Action Input: {"file_path": "api.py", "content": "def get_approval_summary():\n    '''Get approval summary'''\n    data = {'approvalcount': group_data}\n"}
```

**No escaping needed!**

**Result in file:**
```python
def get_approval_summary():
    '''Get approval summary'''
    data = {'approvalcount': group_data}
```

✅ **Correct!**

---

## Key Rules Added

### 1. Include ALL Existing Code
```
1. Include ALL existing code (don't remove any functions/classes)
```

This prevents the agent from accidentally removing code.

### 2. Use Single Quotes
```
2. Use SINGLE quotes ' for Python strings (NOT double quotes ")
```

Single quotes don't need escaping in JSON strings.

### 3. Convert Triple Quotes
```
3. If existing code has triple quotes """, convert to ''' in your output
```

Triple single quotes don't need escaping either.

### 4. Don't Escape
```
4. DO NOT add backslashes before existing quotes
```

Explicit instruction not to escape.

### 5. Keep Everything
```
5. Keep all imports, all functions, all classes - just add your changes
```

Prevents accidental deletion.

---

## Files Changed

### agent/developer_agent.py

**Lines 527-549:** Added "CRITICAL - WHEN MODIFYING EXISTING FILES" section
- 5 explicit rules
- Example showing conversion from `"""` to `'''`
- Emphasis on including ALL code

---

## Testing

### Test 1: File with Docstrings
```bash
# Create file with docstrings
cat > api.py << 'EOF'
def get_data():
    """Get data from API"""
    return {"status": "ok"}
EOF

# Ask agent to add a parameter
curl -X POST http://localhost:8000/query \
  -d '{"query": "Add a timeout parameter to get_data function in api.py"}'

# Verify
cat api.py
```

**Expected:**
```python
def get_data(timeout=30):
    '''Get data from API'''
    return {'status': 'ok'}
```

**Should NOT have:**
- `\"\"\"` (escaped quotes)
- `{\"status\"` (escaped dict keys)
- Missing code

---

### Test 2: File with Multiple Functions
```bash
# Create file
cat > utils.py << 'EOF'
def func1():
    """First function"""
    pass

def func2():
    """Second function"""
    pass

def func3():
    """Third function"""
    pass
EOF

# Ask agent to modify one function
curl -X POST http://localhost:8000/query \
  -d '{"query": "Add a return statement to func2 in utils.py"}'

# Verify
cat utils.py
```

**Expected:**
- All 3 functions still exist
- func2 has return statement
- No escaped quotes
- All docstrings converted to `'''`

---

## Why This Works

### 1. **Explicit Conversion Rule**
The prompt now explicitly says: "If existing code has `"""`, convert to `'''`"

### 2. **Example Showing Conversion**
Shows before/after with the conversion clearly marked.

### 3. **Emphasis on Single Quotes**
Repeated emphasis on using single quotes throughout.

### 4. **Don't Remove Code**
Explicit instruction to keep ALL code.

---

## Summary of Changes

✅ **Added CRITICAL section** - Can't miss it  
✅ **5 explicit rules** - Clear guidelines  
✅ **Conversion example** - Shows `"""` → `'''`  
✅ **Emphasis on completeness** - Keep all code  
✅ **No escaping rule** - Don't add backslashes  

---

## How to Apply

### 1. Restart Server
```bash
uvicorn main:app --reload
```

### 2. Test with Docstrings
```bash
# Create test file
cat > test.py << 'EOF'
def hello():
    """Say hello"""
    print("Hello")
EOF

# Modify it
curl -X POST http://localhost:8000/query \
  -d '{"query": "Add a name parameter to hello function in test.py"}'

# Verify
cat test.py
```

**Should show:**
```python
def hello(name):
    '''Say hello'''
    print('Hello')
```

**NOT:**
```python
def hello(name):
    \"\"\"Say hello\"\"\"
    print(\"Hello\")
```

---

## Expected Behavior

| Original Code | Agent Output | Result |
|---------------|--------------|--------|
| `"""docstring"""` | `'''docstring'''` | No escaping ✓ |
| `"key": value` | `'key': value` | No escaping ✓ |
| `print("hi")` | `print('hi')` | No escaping ✓ |
| All functions | All functions | Nothing removed ✓ |

---

**The agent now correctly handles existing code without escaping or removing content!** 🎉
