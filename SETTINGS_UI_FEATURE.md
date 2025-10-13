# Settings UI Feature

## Overview

Added UI controls to configure **Project Root** and **Vertex Model Name** from the frontend, eliminating the need to manually edit the `.env` file.

---

## Features

### 1. **Model Selection Dropdown**
- Choose between Gemini models:
  - `gemini-2.0-flash-exp` (Latest, fastest)
  - `gemini-1.5-flash` (Fast, efficient)
  - `gemini-1.5-pro` (Most capable)

### 2. **Project Root Browser**
- Browse directories visually
- Navigate through folder structure
- Select project root with one click
- Manual path input also supported

### 3. **Live Agent Reinitialization**
- Settings applied immediately
- Agents reinitialize with new configuration
- No server restart required

---

## How to Use

### Step 1: Open Settings

1. Start the application
2. Click the **⚙️ Settings** button in the controls bar

### Step 2: Select Model

1. Use the **Model Name** dropdown
2. Choose from available Gemini models:
   - **gemini-2.0-flash-exp** - Recommended for speed
   - **gemini-1.5-flash** - Good balance
   - **gemini-1.5-pro** - Best quality

### Step 3: Set Project Root

**Option A: Browse**
1. Click **📁 Browse** button
2. Navigate through directories
3. Double-click folders to open them
4. Click **Select** on desired folder
5. Or click **Select Current Directory**

**Option B: Manual Entry**
1. Type or paste path directly in text field
2. Path must exist on your system

### Step 4: Save

1. Click **💾 Save Settings**
2. Wait for confirmation
3. Agents will reinitialize automatically

---

## UI Components

### Settings Panel

```
⚙️ Settings
├── Model Name: [Dropdown]
│   └── gemini-2.0-flash-exp
│   └── gemini-1.5-flash
│   └── gemini-1.5-pro
├── Project Root: [Text Input] [📁 Browse]
└── [💾 Save Settings] [Cancel]
```

### Directory Browser

```
📁 Browse Directory                     [✕]
Current: /home/user/projects
├── 📁 .. (parent)
├── 📁 project1              [Select]
├── 📁 project2              [Select]
└── 📁 project3              [Select]
[Select Current Directory]
```

---

## Backend API

### GET /settings

Get current settings.

**Response:**
```json
{
  "project_root": "/path/to/project",
  "model_name": "gemini-2.0-flash-exp",
  "available_models": [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
  ]
}
```

---

### POST /settings

Update settings and reinitialize agents.

**Request:**
```json
{
  "project_root": "/new/path/to/project",
  "model_name": "gemini-1.5-pro"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Settings updated successfully",
  "project_root": "/new/path/to/project",
  "model_name": "gemini-1.5-pro"
}
```

**Errors:**
- `400` - Invalid path or model name
- `500` - Server error during reinitialization

---

### GET /browse-directory

Browse directories for selection.

**Query Parameters:**
- `path` (optional) - Directory to browse (defaults to home)

**Response:**
```json
{
  "current_path": "/home/user/projects",
  "parent_path": "/home/user",
  "items": [
    {
      "name": "project1",
      "path": "/home/user/projects/project1",
      "type": "directory"
    }
  ]
}
```

---

## Implementation Details

### Backend Changes (`main.py`)

#### 1. **New Models**

```python
class SettingsRequest(BaseModel):
    project_root: Optional[str] = None
    model_name: Optional[str] = None

class SettingsResponse(BaseModel):
    project_root: str
    model_name: str
    available_models: List[str]
```

#### 2. **Settings Endpoints**

- `GET /settings` - Retrieve current settings
- `POST /settings` - Update and reinitialize
- `GET /browse-directory` - Browse filesystem

#### 3. **Agent Reinitialization**

```python
# Update environment variables
os.environ["PROJECT_ROOT"] = settings.project_root
os.environ["VERTEX_MODEL_NAME"] = settings.model_name

# Reinitialize agents
agent = DeveloperAgent(project_root=settings.project_root, auto_approve=auto_approve)
dev_lead_agent = DevLeadAgent()
```

---

### Frontend Changes (`ui/src/App.tsx`)

#### 1. **New State Variables**

```typescript
const [showSettings, setShowSettings] = useState<boolean>(false)
const [projectRoot, setProjectRoot] = useState<string>('')
const [modelName, setModelName] = useState<string>('gemini-2.0-flash-exp')
const [availableModels, setAvailableModels] = useState<string[]>([])
const [showBrowser, setShowBrowser] = useState<boolean>(false)
const [currentPath, setCurrentPath] = useState<string>('')
const [parentPath, setParentPath] = useState<string | null>(null)
const [directories, setDirectories] = useState<DirectoryItem[]>([])
```

#### 2. **New Functions**

- `loadSettings()` - Load current settings on startup
- `saveSettings()` - Save and apply new settings
- `browseDirectory(path)` - Browse filesystem
- `selectDirectory(path)` - Select a directory

#### 3. **UI Components**

- Settings panel with model dropdown and path input
- Directory browser modal with navigation
- Save/Cancel buttons

---

### CSS Changes (`ui/src/App.css`)

Added styles for:
- `.settings-panel` - Settings container
- `.setting-group` - Individual setting
- `.directory-browser` - Modal browser
- `.directory-item` - Directory list items
- `.btn-small` - Small action buttons

---

## Validation

### Project Root Validation

**Backend checks:**
1. Path must exist
2. Path must be absolute (converted if relative)
3. Path must be accessible

**Error handling:**
```json
{
  "status_code": 400,
  "detail": "Project root path does not exist: /invalid/path"
}
```

---

### Model Name Validation

**Valid models:**
- `gemini-2.0-flash-exp`
- `gemini-1.5-flash`
- `gemini-1.5-pro`

**Error handling:**
```json
{
  "status_code": 400,
  "detail": "Invalid model name. Must be one of: gemini-2.0-flash-exp, gemini-1.5-flash, gemini-1.5-pro"
}
```

---

## Security Considerations

### 1. **Path Traversal Protection**

- Only directories are listed
- Parent directory navigation is controlled
- Absolute paths are enforced

### 2. **Permission Handling**

```python
try:
    for item in sorted(os.listdir(path)):
        # List items
except PermissionError:
    pass  # Skip inaccessible directories
```

### 3. **Input Validation**

- Model name must be in allowed list
- Path must exist before saving
- All inputs are sanitized

---

## Testing

### Test 1: Change Model

1. Open Settings
2. Select **gemini-1.5-pro**
3. Click Save
4. Verify: "Settings saved successfully!"
5. Send a query
6. Check backend logs for model name

**Expected:** Agent uses new model

---

### Test 2: Change Project Root

1. Open Settings
2. Click Browse
3. Navigate to desired directory
4. Click Select
5. Click Save
6. Send: "List files in current directory"

**Expected:** Files from new project root

---

### Test 3: Browse Directories

1. Click Browse
2. Verify current path shown
3. Double-click a folder
4. Verify navigation works
5. Click ".." to go up
6. Verify parent navigation

**Expected:** Smooth navigation

---

### Test 4: Manual Path Entry

1. Open Settings
2. Type path: `/home/user/myproject`
3. Click Save

**Expected:** 
- If path exists: Success
- If path doesn't exist: Error message

---

### Test 5: Invalid Model

1. Use API directly:
```bash
curl -X POST http://localhost:8000/settings \
  -H "Content-Type: application/json" \
  -d '{"model_name": "invalid-model"}'
```

**Expected:** 400 error with valid models list

---

## Troubleshooting

### Issue: Settings Not Saving

**Check:**
1. Backend is running
2. No console errors
3. Path exists and is accessible

**Fix:**
```bash
# Check backend logs
tail -f logs/uvicorn.log
```

---

### Issue: Directory Browser Empty

**Possible causes:**
1. No subdirectories in current path
2. Permission denied

**Fix:**
- Navigate to a different directory
- Check file permissions

---

### Issue: Agent Not Using New Model

**Check:**
1. Settings saved successfully
2. Backend reinitialized agents
3. Environment variable updated

**Verify:**
```python
# In backend logs
print(os.getenv("VERTEX_MODEL_NAME"))
```

---

## Files Modified

### Backend
1. **`main.py`**
   - Added `SettingsRequest`, `SettingsResponse` models
   - Added `GET /settings` endpoint
   - Added `POST /settings` endpoint
   - Added `GET /browse-directory` endpoint
   - Agent reinitialization logic

### Frontend
1. **`ui/src/App.tsx`**
   - Added settings state variables
   - Added `loadSettings()`, `saveSettings()` functions
   - Added `browseDirectory()`, `selectDirectory()` functions
   - Added settings panel UI
   - Added directory browser UI

2. **`ui/src/App.css`**
   - Added `.settings-panel` styles
   - Added `.directory-browser` styles
   - Added `.setting-group`, `.directory-item` styles

---

## Benefits

### ✅ **User-Friendly**
- No need to edit `.env` file
- Visual directory browsing
- Immediate feedback

### ✅ **Flexible**
- Switch models on the fly
- Change project root without restart
- Test different configurations easily

### ✅ **Safe**
- Path validation
- Permission handling
- Error messages

### ✅ **Persistent**
- Settings saved to environment
- Survive until server restart
- Can be made persistent with file storage

---

## Future Enhancements

### 1. **Persistent Storage**
Save settings to a config file so they survive server restarts.

```python
# Save to config.json
with open('config.json', 'w') as f:
    json.dump({
        'project_root': project_root,
        'model_name': model_name
    }, f)
```

### 2. **Multiple Project Profiles**
Save and switch between different project configurations.

### 3. **Model Parameters**
Expose temperature, top_p, top_k settings in UI.

### 4. **Recent Paths**
Remember recently used project roots.

### 5. **Auto-Detect Projects**
Scan for common project markers (git, package.json, etc.).

---

## Summary

✅ **Model selection** via dropdown  
✅ **Project root** via browser or manual entry  
✅ **Live reinitialization** without restart  
✅ **Visual directory browsing**  
✅ **Input validation** and error handling  
✅ **Clean, intuitive UI**  

**Users can now configure the agent entirely from the UI!** 🎉
