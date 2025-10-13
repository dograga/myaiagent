# Rebuild Frontend - Quick Guide

## Issue

You made changes to the frontend code but don't see them in the browser because the frontend needs to be rebuilt.

---

## Solution: Rebuild Frontend

### Step 1: Stop Current Frontend

If the frontend is running, press **Ctrl+C** in the terminal where `npm run dev` is running.

---

### Step 2: Rebuild

```bash
cd ui
npm run dev
```

**Expected output:**
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:5173/
➜  Network: use --host to expose
```

---

### Step 3: Hard Refresh Browser

After the frontend restarts:

**Windows/Linux:**
- Press **Ctrl+Shift+R** or **Ctrl+F5**

**Mac:**
- Press **Cmd+Shift+R**

Or:
1. Open DevTools (F12)
2. Right-click the refresh button
3. Select "Empty Cache and Hard Reload"

---

## Verify Changes

### 1. Check Settings Button

Look at the controls bar, you should see:
```
[New Session] [Clear History] [Reload History] [⚙️ Settings]
```

**Click ⚙️ Settings** - A panel should appear below with:
- Model Name dropdown
- Project Root input with Browse button
- Save/Cancel buttons

---

### 2. Check Textarea Behavior

**Test Enter Key:**
1. Click in the input field
2. Type: `Line 1`
3. Press **Enter** (just Enter, no Shift)
4. **Expected:** New line appears (cursor moves down)
5. Type: `Line 2`
6. Press **Shift+Enter**
7. **Expected:** Message is sent

**New behavior:**
- **Enter** = New line
- **Shift+Enter** = Send message
- **Click Send button** = Send message

---

## If Settings Still Not Visible

### Check Browser Console

1. Press **F12** to open DevTools
2. Click **Console** tab
3. Look for errors (red text)
4. Share any errors you see

---

### Check Network Tab

1. In DevTools, click **Network** tab
2. Refresh page
3. Look for `/settings` request
4. Check if it returns data

**Expected response:**
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

### Verify Backend is Running

```bash
# In another terminal
curl http://localhost:8000/settings
```

**Expected:** JSON response with settings

**If error:** Backend might not be running
```bash
# Start backend
uvicorn main:app --reload
```

---

## Complete Restart (If Needed)

If changes still don't appear:

### 1. Stop Everything

- Stop frontend (Ctrl+C)
- Stop backend (Ctrl+C)

### 2. Clear Cache

```bash
cd ui
rm -rf node_modules/.vite
# or on Windows:
# rmdir /s /q node_modules\.vite
```

### 3. Restart Backend

```bash
cd c:\Users\gaura\Downloads\repo\myaiagent
uvicorn main:app --reload
```

### 4. Restart Frontend

```bash
cd ui
npm run dev
```

### 5. Hard Refresh Browser

**Ctrl+Shift+R** (or **Cmd+Shift+R** on Mac)

---

## What You Should See

### Settings Panel (After clicking ⚙️ Settings)

```
⚙️ Settings

Model Name:
[Dropdown: gemini-2.0-flash-exp ▼]
Select the Gemini model to use for AI responses

Project Root:
[/current/path/to/project          ] [📁 Browse]
The root directory where the agent can read/write files

[💾 Save Settings] [Cancel]
```

---

### Directory Browser (After clicking 📁 Browse)

```
📁 Browse Directory                                    [✕]
Current: /home/user

📁 .. (parent directory)
📁 Documents                                    [Select]
📁 Downloads                                    [Select]
📁 projects                                     [Select]

[Select Current Directory]
```

---

### Textarea Input

```
┌─────────────────────────────────────────────────┐
│ Ask me to help with your code...               │
│                                                 │
│ Press Shift+Enter to send, Enter for new line. │
└─────────────────────────────────────────────────┘
                                          [Send]
```

**Behavior:**
- Type and press **Enter** → New line
- Type and press **Shift+Enter** → Send message
- Click **Send** button → Send message

---

## Troubleshooting

### Issue: Settings button exists but panel doesn't open

**Check:**
1. Click the button - does `showSettings` state change?
2. Open React DevTools
3. Find `App` component
4. Check `showSettings` value

**Fix:** Might be a CSS issue hiding the panel

---

### Issue: Textarea still submits on Enter

**Check:**
1. View page source
2. Search for `onKeyDown`
3. Verify it checks `e.shiftKey`

**Fix:** Frontend not rebuilt - follow rebuild steps above

---

### Issue: Models dropdown is empty

**Check:**
1. Open DevTools Console
2. Look for errors
3. Check if `availableModels` state is populated

**Fix:** Backend `/settings` endpoint might not be working

---

## Quick Test Commands

### Test Backend Settings Endpoint

```bash
curl http://localhost:8000/settings
```

**Expected:**
```json
{
  "project_root": "...",
  "model_name": "gemini-2.0-flash-exp",
  "available_models": ["gemini-2.0-flash-exp", "gemini-1.5-flash", "gemini-1.5-pro"]
}
```

---

### Test Directory Browser

```bash
curl http://localhost:8000/browse-directory
```

**Expected:**
```json
{
  "current_path": "/home/user",
  "parent_path": "/home",
  "items": [...]
}
```

---

## Summary

**To see changes:**
1. ✅ Stop frontend (Ctrl+C)
2. ✅ Restart frontend (`npm run dev`)
3. ✅ Hard refresh browser (Ctrl+Shift+R)
4. ✅ Click ⚙️ Settings button
5. ✅ Test Enter key (new line) vs Shift+Enter (send)

**Keyboard shortcuts:**
- **Enter** = New line in textarea
- **Shift+Enter** = Send message
- **Ctrl+Shift+R** = Hard refresh browser

**If still not working:**
- Check browser console for errors
- Verify backend is running
- Check network tab for API calls
- Try complete restart (stop everything, clear cache, restart)

---

**After rebuild, you should see the Settings button and proper textarea behavior!** 🎉
