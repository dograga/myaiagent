# Approval Mode Guide

## Overview

The Developer Assistant supports two modes of operation:

1. **AUTO-APPROVE Mode** (Default) - Agent executes changes immediately
2. **APPROVAL Mode** - Agent describes changes and waits for explicit approval

## Configuration

### Setting the Mode

Add to your `.env` file:

```env
# Auto-approve mode (default)
AUTO_APPROVE=true

# OR Approval mode
AUTO_APPROVE=false
```

Restart the server after changing this setting.

### Check Current Mode

```bash
curl http://localhost:8000/health
```

Response will include:
```json
{
  "config": {
    "auto_approve": true,
    "project_root": "/path/to/project"
  }
}
```

## AUTO-APPROVE Mode (Default)

### Behavior

When `AUTO_APPROVE=true`:
- Agent **immediately executes** all requested changes
- No confirmation needed
- Agent reports what it **DID**, not what it **WILL** do
- Faster workflow for trusted operations

### Example Interaction

**You:** "Create a file called test.py with a hello function"

**Agent:** 
```
✓ I have created the file test.py with the following content:

def hello():
    print("Hello, World!")

The file has been successfully written to test.py
```

**You:** "Add a goodbye function"

**Agent:**
```
✓ I have added the goodbye function to test.py. The file now contains:

def hello():
    print("Hello, World!")

def goodbye():
    print("Goodbye!")
```

### When to Use

- ✅ Working in a safe development environment
- ✅ Making small, incremental changes
- ✅ You trust the agent's decisions
- ✅ You want fast iteration
- ✅ Changes are easily reversible (use version control!)

### Safety Tips

1. **Use Version Control**: Always work in a Git repository
   ```bash
   git init
   git add .
   git commit -m "Before agent changes"
   ```

2. **Set PROJECT_ROOT**: Limit agent to a specific directory
   ```env
   PROJECT_ROOT=/path/to/safe/directory
   ```

3. **Review Changes**: Check what the agent did
   ```bash
   git diff
   ```

4. **Backup Important Files**: Before major changes

## APPROVAL Mode

### Behavior

When `AUTO_APPROVE=false`:
- Agent **describes** what it would do
- Waits for your explicit approval
- Only executes after you confirm
- Safer for production or critical files

### Example Interaction

**You:** "Create a file called config.py with database settings"

**Agent:**
```
I would create a file called config.py with the following content:

DATABASE_HOST = "localhost"
DATABASE_PORT = 5432
DATABASE_NAME = "myapp"

Would you like me to proceed with creating this file?
```

**You:** "Yes, go ahead"

**Agent:**
```
✓ I have created config.py with the database settings.
```

### When to Use

- ✅ Working with production code
- ✅ Making significant changes
- ✅ Modifying critical files
- ✅ You want to review before execution
- ✅ Learning what the agent will do

## Comparison

| Feature | AUTO-APPROVE | APPROVAL |
|---------|-------------|----------|
| Speed | ⚡ Fast | 🐢 Slower (requires confirmation) |
| Safety | ⚠️ Less safe | ✅ Safer |
| Workflow | Immediate execution | Describe → Approve → Execute |
| Best For | Development | Production |
| User Input | One request | Two steps (request + approval) |

## Switching Modes

### During Development

```env
# Fast iteration
AUTO_APPROVE=true
```

### Before Deployment

```env
# Careful changes
AUTO_APPROVE=false
```

### Per-Session Control (Future Enhancement)

Currently, the mode is global. In a future version, you could specify per-query:

```json
{
  "query": "Delete all test files",
  "auto_approve": false  // Override global setting
}
```

## Troubleshooting

### Agent Not Executing in AUTO-APPROVE Mode

**Symptoms:**
- Agent describes changes but doesn't execute
- Agent says "I would..." instead of "I have..."

**Solutions:**

1. **Check Configuration:**
   ```bash
   curl http://localhost:8000/health | jq '.config.auto_approve'
   ```
   Should return `true`

2. **Restart Server:**
   ```bash
   # Stop the server (Ctrl+C)
   # Start again
   uvicorn main:app --reload
   ```

3. **Verify .env File:**
   ```bash
   cat .env | grep AUTO_APPROVE
   ```
   Should show `AUTO_APPROVE=true`

4. **Clear Prompt:**
   Be explicit in your requests:
   ```
   ❌ "What changes would you make to..."
   ✅ "Create a file..."
   ✅ "Update the function..."
   ✅ "Delete the old code..."
   ```

### Agent Executing Without Approval in APPROVAL Mode

**Symptoms:**
- Agent executes immediately when you want approval first

**Solutions:**

1. **Set AUTO_APPROVE=false** in `.env`
2. **Restart the server**
3. **Verify with health check**

## Best Practices

### 1. Start with AUTO-APPROVE

For new projects and development:
```env
AUTO_APPROVE=true
PROJECT_ROOT=./dev-sandbox
```

### 2. Use Version Control

Always:
```bash
git init
git add .
git commit -m "checkpoint"
```

After agent changes:
```bash
git diff  # Review changes
git add . # If good
git commit -m "Agent: added feature X"
# OR
git reset --hard  # If bad, revert
```

### 3. Limit Scope

Set PROJECT_ROOT to limit where agent can make changes:
```env
PROJECT_ROOT=./src/components  # Only this directory
```

### 4. Test in Sandbox First

```env
PROJECT_ROOT=./sandbox
AUTO_APPROVE=true
```

Test your queries here, then switch to real project.

### 5. Switch to APPROVAL for Risky Operations

```env
# For deleting files, major refactoring, etc.
AUTO_APPROVE=false
```

## Examples

### AUTO-APPROVE Workflow

```bash
# Session 1: Quick development
You: "Create a calculator.py with add and subtract"
Agent: ✓ Created calculator.py with add() and subtract()

You: "Add multiply and divide"  
Agent: ✓ Added multiply() and divide() to calculator.py

You: "Add error handling for division by zero"
Agent: ✓ Updated divide() with try-except for ZeroDivisionError

# All done in 3 messages!
```

### APPROVAL Workflow

```bash
# Session 2: Careful production change
You: "Update the database connection string in config.py"
Agent: I would change line 5 from:
       DATABASE_URL = "localhost"
       to:
       DATABASE_URL = "prod-db.example.com"
       
       Should I proceed?

You: "Yes"
Agent: ✓ Updated config.py with new database URL

# Reviewed before execution
```

## Security Considerations

### AUTO-APPROVE Risks

- ⚠️ Agent could delete important files
- ⚠️ Agent could overwrite existing code
- ⚠️ Mistakes are executed immediately

**Mitigations:**
- Use version control (Git)
- Set PROJECT_ROOT to limit scope
- Work in development environment
- Regular backups

### APPROVAL Benefits

- ✅ Review before execution
- ✅ Catch mistakes before they happen
- ✅ Learn what agent plans to do
- ✅ Safer for production

**Trade-offs:**
- Slower workflow
- More user interaction required

## Future Enhancements

Planned features:

1. **Per-Query Override:**
   ```json
   {"query": "...", "auto_approve": false}
   ```

2. **Approval Levels:**
   - `auto` - Execute everything
   - `confirm_destructive` - Only confirm deletes
   - `confirm_all` - Confirm everything

3. **Dry-Run Mode:**
   ```json
   {"query": "...", "dry_run": true}
   ```
   Shows what would happen without executing

4. **Undo Command:**
   ```
   "Undo the last change"
   ```

## Summary

- **Default:** `AUTO_APPROVE=true` for fast development
- **Production:** `AUTO_APPROVE=false` for safety
- **Always:** Use version control
- **Limit:** Set PROJECT_ROOT appropriately
- **Switch:** Change mode based on task risk level

Choose the mode that matches your workflow and risk tolerance!
