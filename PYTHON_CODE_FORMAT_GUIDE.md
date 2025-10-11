# Python Code Format Guide for Agent

## Issue

Agent was escaping quotes in Python code incorrectly, causing:
- `"""docstring"""` → `\"\"\"docstring\"\"\"`
- `print("hello")` → `print(\"hello\")`
- `f"value: {x}"` → `f\"value: {{x}}\"`

This breaks Python syntax!

## Root Cause

The prompt told the agent to "use single quotes" but didn't explain how to handle existing Python code with double quotes, docstrings, or f-strings.

## Solution

### Updated Prompt Rules

```
KEY RULES FOR PYTHON CODE:
- Use \n for line breaks (NOT actual newlines)
- For Python print/f-strings: Use SINGLE quotes like print('hello') or f'value: {x}'
- For Python docstrings: Use TRIPLE SINGLE quotes like '''docstring''' (NOT \"\"\"docstring\"\"\")
- For Python comments: Use # normally, no escaping needed
- Keep JSON on ONE line
- ALWAYS close the JSON string with "}" at the end
- DO NOT add backslashes before quotes that are already in Python code
- COMPLETE FORMAT: {"file_path": "file.py", "content": "code here"}
```

## Correct Examples

### Example 1: Simple Function with Print

**CORRECT:**
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

**CORRECT:**
```json
{"file_path": "calc.py", "content": "def add(a, b):\n    '''Add two numbers'''\n    return a + b\n"}
```

**Result:**
```python
def add(a, b):
    '''Add two numbers'''
    return a + b
```

**WRONG:**
```json
{"file_path": "calc.py", "content": "def add(a, b):\n    \\\"\\\"\\\"Add two numbers\\\"\\\"\\\"\n    return a + b\n"}
```

This would create:
```python
def add(a, b):
    \"\"\"Add two numbers\"\"\"  # BROKEN!
    return a + b
```

---

### Example 3: Function with F-String

**CORRECT:**
```json
{"file_path": "greet.py", "content": "def greet(name):\n    message = f'Hello, {name}!'\n    print(message)\n"}
```

**Result:**
```python
def greet(name):
    message = f'Hello, {name}!'
    print(message)
```

**WRONG:**
```json
{"file_path": "greet.py", "content": "def greet(name):\n    message = f\\\"Hello, {name}!\\\"\n    print(message)\n"}
```

---

### Example 4: Function with Multi-line Docstring

**CORRECT:**
```json
{"file_path": "func.py", "content": "def calculate(x, y):\n    '''\n    Calculate something.\n    \n    Args:\n        x: First number\n        y: Second number\n    '''\n    return x + y\n"}
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

### Example 5: Function with Exception Handling

**CORRECT:**
```json
{"file_path": "safe.py", "content": "def divide(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        raise ValueError(f'Cannot divide by zero')\n"}
```

**Result:**
```python
def divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        raise ValueError(f'Cannot divide by zero')
```

**WRONG:**
```json
{"file_path": "safe.py", "content": "def divide(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        raise ValueError(f\\'Cannot divide by zero\\')\n"}
```

---

### Example 6: Class with Docstring

**CORRECT:**
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

### Example 7: Function with Comments

**CORRECT:**
```json
{"file_path": "math.py", "content": "def factorial(n):\n    # Base case\n    if n == 0:\n        return 1\n    # Recursive case\n    return n * factorial(n - 1)\n"}
```

**Result:**
```python
def factorial(n):
    # Base case
    if n == 0:
        return 1
    # Recursive case
    return n * factorial(n - 1)
```

---

## Key Principles

### 1. Use Single Quotes for Python Strings

**Why?** Single quotes don't need escaping in JSON strings.

```json
✅ "print('hello')"
❌ "print(\"hello\")"  // Requires escaping
```

### 2. Use Triple Single Quotes for Docstrings

**Why?** Triple single quotes don't need escaping in JSON strings.

```json
✅ "'''This is a docstring'''"
❌ "\"\"\"This is a docstring\"\"\""  // Requires escaping
```

### 3. Never Add Backslashes to Python Code

**Why?** The JSON parser handles escaping, not you.

```json
✅ "raise ValueError(f'Error: {msg}')"
❌ "raise ValueError(f\\'Error: {msg}\\')"  // Wrong!
```

### 4. Use \n for Newlines

**Why?** JSON strings must be on one line.

```json
✅ "def hello():\n    print('hi')"
❌ "def hello():
    print('hi')"  // Invalid JSON!
```

---

## Common Mistakes to Avoid

### Mistake 1: Escaping Triple Quotes

**WRONG:**
```json
{"content": "def func():\n    \\\"\\\"\\\"Docstring\\\"\\\"\\\"\n    pass"}
```

**CORRECT:**
```json
{"content": "def func():\n    '''Docstring'''\n    pass"}
```

---

### Mistake 2: Escaping F-String Quotes

**WRONG:**
```json
{"content": "message = f\\\"Hello {name}\\\""}
```

**CORRECT:**
```json
{"content": "message = f'Hello {name}'"}
```

---

### Mistake 3: Escaping Print Quotes

**WRONG:**
```json
{"content": "print(\\\"Hello\\\")"}
```

**CORRECT:**
```json
{"content": "print('Hello')"}
```

---

### Mistake 4: Adding Extra Backslashes

**WRONG:**
```json
{"content": "raise ValueError(f\\'Error\\')"}
```

**CORRECT:**
```json
{"content": "raise ValueError(f'Error')"}
```

---

## How the Agent Should Think

### When Creating Python Code:

1. **Write the Python code mentally** with proper syntax
2. **Convert to JSON format:**
   - Replace newlines with `\n`
   - Use single quotes for strings
   - Use triple single quotes for docstrings
   - Keep everything on one line
3. **DO NOT add extra escaping** - the JSON parser handles it

### Example Thought Process:

**User Request:** "Create a function that greets a user"

**Agent Thinks:**
```python
def greet(name):
    '''Greet a user by name'''
    return f'Hello, {name}!'
```

**Agent Converts to JSON:**
```json
{"file_path": "greet.py", "content": "def greet(name):\n    '''Greet a user by name'''\n    return f'Hello, {name}!'\n"}
```

**Agent Does NOT:**
```json
{"file_path": "greet.py", "content": "def greet(name):\n    \\\"\\\"\\\"Greet a user by name\\\"\\\"\\\"\n    return f\\\"Hello, {name}!\\\"\n"}
```

---

## Testing

### Test 1: Docstring

**Request:** "Create a function with a docstring"

**Expected JSON:**
```json
{"file_path": "test.py", "content": "def test():\n    '''This is a test'''\n    pass\n"}
```

**Expected File:**
```python
def test():
    '''This is a test'''
    pass
```

### Test 2: F-String

**Request:** "Create a function that uses f-string"

**Expected JSON:**
```json
{"file_path": "format.py", "content": "def format_name(first, last):\n    return f'{first} {last}'\n"}
```

**Expected File:**
```python
def format_name(first, last):
    return f'{first} {last}'
```

### Test 3: Exception with Message

**Request:** "Create a function that raises an error with a message"

**Expected JSON:**
```json
{"file_path": "error.py", "content": "def check(value):\n    if value < 0:\n        raise ValueError(f'Value must be positive, got {value}')\n"}
```

**Expected File:**
```python
def check(value):
    if value < 0:
        raise ValueError(f'Value must be positive, got {value}')
```

---

## Summary

✅ **Use single quotes** for Python strings: `print('hello')`  
✅ **Use triple single quotes** for docstrings: `'''docstring'''`  
✅ **Use \n** for newlines: `def func():\n    pass`  
✅ **DO NOT escape** Python code: `f'value: {x}'` not `f\'value: {x}\'`  
✅ **Keep JSON on one line** with proper closing: `{"file_path": "...", "content": "..."}`  

❌ **DO NOT use** `\"\"\"docstring\"\"\"`  
❌ **DO NOT use** `print(\"hello\")`  
❌ **DO NOT add** extra backslashes to Python code  

---

**The agent now understands how to format Python code correctly in JSON!** 🎉
