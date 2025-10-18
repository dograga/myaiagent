# Bug Fixes: Directory Browser and Settings

## Issues Fixed

### Issue 1: Directory Browser - Cannot Drill Down into Subfolders
**Problem**: Users could only see first-level folders and couldn't navigate into subfolders.

**Root Cause**: The UI required a double-click (`onDoubleClick`) to navigate into folders, which was not intuitive and not clearly communicated to users.

**Solution**: Changed to single-click navigation on the folder name.

**File Modified**: `ui/src/App.tsx`

**Changes**:
- Removed `onDoubleClick` from the directory item div
- Added `onClick` handler to the folder name span
- Made the folder name clickable with visual feedback (`cursor: 'pointer'`)
- Added `e.stopPropagation()` to the Select button to prevent navigation when clicking Select

**Before**:
```tsx
<div 
  className="directory-item"
  onDoubleClick={() => browseDirectory(dir.path)}
>
  <span>📁 {dir.name}</span>
  <button onClick={() => selectDirectory(dir.path)}>Select</button>
</div>
```

**After**:
```tsx
<div className="directory-item">
  <span onClick={() => browseDirectory(dir.path)} style={{ cursor: 'pointer', flex: 1 }}>
    📁 {dir.name}
  </span>
  <button onClick={(e) => {
    e.stopPropagation()
    selectDirectory(dir.path)
  }}>
    Select
  </button>
</div>
```

**User Experience**:
- Click on folder name (📁 FolderName) to navigate into it
- Click "Select" button to choose that folder as project root
- Click "📁 .." to go up one level
- Click "Select Current Directory" to choose the currently displayed path

---

### Issue 2: Backend Not Updating project_root
**Problem**: When updating settings from the UI, the project_root would revert to the value in the .env file instead of keeping the user's selection.

**Root Cause**: When the model name was updated, the backend code read `project_root` from the environment variable (`os.getenv("PROJECT_ROOT")`) instead of preserving the current agent's `project_root` value.

**Solution**: Use the current agent's `project_root` when reinitializing agents for model changes.

**File Modified**: `main.py`

**Changes**:
Lines 574-576 changed from:
```python
auto_approve = os.getenv("AUTO_APPROVE", "true").lower() in ("true", "1", "yes")
project_root = os.getenv("PROJECT_ROOT", os.getcwd())
if not os.path.isabs(project_root):
    project_root = os.path.abspath(project_root)
```

To:
```python
auto_approve = os.getenv("AUTO_APPROVE", "true").lower() in ("true", "1", "yes")
current_project_root = developer_agent.project_root
```

**Why This Works**:
1. When user updates project_root via UI, it's saved in `developer_agent.project_root` and `devops_agent.project_root`
2. When model name is changed, agents are reinitialized
3. Now we use `developer_agent.project_root` (the current value) instead of reading from env
4. This preserves the user's project_root selection across model changes

---

## Testing

### Test Case 1: Directory Navigation
1. Click "📁 Browse" button in settings
2. Click on any folder name (e.g., "📁 ui")
3. Verify you can see subfolders inside
4. Click "📁 .." to go back up
5. Navigate to desired folder
6. Click "Select" or "Select Current Directory"
7. Verify the path is updated in the Project Root input field

### Test Case 2: Settings Persistence
1. Browse and select a project root (e.g., `C:\Users\gaura\Downloads\repo\myaiagent\ui`)
2. Click "💾 Save Settings"
3. Verify success message
4. Change the model (e.g., from gemini-2.0-flash-exp to gemini-1.5-flash)
5. Click "💾 Save Settings"
6. Verify the project root is STILL the path you selected (not reverted to .env value)

### Test Case 3: Combined Test
1. Set project root to a custom path
2. Change model name
3. Save settings
4. Send a query to the agent
5. Verify the agent operates on the correct project root (not the .env default)

---

## Additional Notes

### Project Root Priority
The project root is now determined in this order:
1. **User selection via UI** (highest priority) - stored in agent instances
2. **Environment variable** (.env file) - used only on initial startup
3. **Current working directory** - fallback if no env var

### Session Persistence
- Project root changes persist for the current backend session
- If you restart the backend server, it will revert to the .env value
- To make changes permanent, update the .env file

### Future Improvements
Consider adding:
- Persistence of UI settings to a config file
- Visual indicator showing which folder is currently selected
- Breadcrumb navigation in the directory browser
- Keyboard shortcuts (Enter to navigate, Escape to close)
