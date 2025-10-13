# Troubleshoot UI - Settings Not Showing

## Your Issue

- Ran `npm run dev`
- Opened `http://localhost:3000`
- **Settings button not visible**
- **Enter key still submits** (instead of new line)

**This means you're seeing the OLD cached version of the UI.**

---

## Solution: Clear Cache & Rebuild

### Step 1: Stop Frontend

Press **Ctrl+C** in the terminal where `npm run dev` is running.

---

### Step 2: Clear Vite Cache

**Option A: Use the script (Easiest)**
```bash
cd c:\Users\gaura\Downloads\repo\myaiagent\ui
clear-cache.bat
```

**Option B: Manual**
```bash
cd c:\Users\gaura\Downloads\repo\myaiagent\ui
rmdir /s /q node_modules\.vite
```

---

### Step 3: Restart Frontend

```bash
npm run dev
```

Wait for:
```
VITE v5.x.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

---

### Step 4: HARD REFRESH Browser

**This is the most important step!**

**Windows:**
1. Open `http://localhost:3000`
2. Press **Ctrl+Shift+R** (or **Ctrl+F5**)
3. Or: Right-click refresh button → "Empty Cache and Hard Reload"

**Alternative:**
1. Press **F12** to open DevTools
2. Right-click the refresh button in the browser
3. Select **"Empty Cache and Hard Reload"**

---

## Verify the Changes

After hard refresh, you should see:

### 1. Settings Button

Look at the controls bar (below the header):
```
[New Session] [Clear History] [Reload History] [⚙️ Settings] [☑ Show Thought Process] [☑ 👔 Dev Lead Review] [☑ ⚡ Streaming]
```

**If you see ⚙️ Settings button** → Success! ✅

**If you DON'T see it** → Browser is still using cached version

---

### 2. Textarea (Multi-line Input)

Look at the input field at the bottom:
- Should be **3 rows tall** (not a single line)
- Placeholder should say: "Press Shift+Enter to send, Enter for new line."

**Test:**
1. Click in the input field
2. Type: `Line 1`
3. Press **Enter** (just Enter, no Shift)
4. **Expected:** Cursor moves to new line (message NOT sent)
5. Type: `Line 2`
6. Press **Shift+Enter**
7. **Expected:** Message is sent

---

## If Still Not Working

### Check 1: Verify You're on the Right Port

Make sure you're accessing:
```
http://localhost:3000
```

NOT:
- `http://localhost:5173`
- `http://localhost:8000`

---

### Check 2: Inspect the Page Source

1. Right-click on the page
2. Select "View Page Source"
3. Press **Ctrl+F** and search for: `Settings`
4. You should find: `⚙️ Settings`

**If you DON'T find it:**
- The old code is still being served
- Try clearing browser cache more aggressively (see below)

---

### Check 3: Clear Browser Cache Completely

**Chrome/Edge:**
1. Press **Ctrl+Shift+Delete**
2. Select "Cached images and files"
3. Time range: "Last hour"
4. Click "Clear data"
5. Refresh page

**Firefox:**
1. Press **Ctrl+Shift+Delete**
2. Select "Cache"
3. Click "Clear Now"
4. Refresh page

---

### Check 4: Try Incognito/Private Mode

1. Open a new **Incognito/Private window**
2. Go to `http://localhost:3000`
3. Check if Settings button appears

**If it appears in Incognito:**
- Your regular browser has aggressive caching
- Clear all browser cache (not just for this site)

---

### Check 5: Verify the Code is Correct

Open DevTools Console (F12) and run:
```javascript
// Check if Settings button exists in the DOM
document.querySelector('button:contains("Settings")')
```

Or search the page source for "⚙️ Settings"

---

## Nuclear Option: Complete Rebuild

If nothing else works:

### Step 1: Stop Everything
```bash
# Stop frontend (Ctrl+C)
# Stop backend (Ctrl+C)
```

### Step 2: Clear Everything
```bash
cd c:\Users\gaura\Downloads\repo\myaiagent\ui

# Clear Vite cache
rmdir /s /q node_modules\.vite

# Clear dist
rmdir /s /q dist

# Optional: Reinstall dependencies
rmdir /s /q node_modules
npm install
```

### Step 3: Restart Backend
```bash
cd c:\Users\gaura\Downloads\repo\myaiagent
uvicorn main:app --reload
```

### Step 4: Restart Frontend
```bash
cd ui
npm run dev
```

### Step 5: Clear Browser Completely
1. Close ALL browser tabs
2. Clear all browsing data (Ctrl+Shift+Delete)
3. Close browser completely
4. Reopen browser
5. Go to `http://localhost:3000`

---

## Verify Backend Changes

The Settings button calls backend endpoints. Make sure backend has the changes:

```bash
# Test settings endpoint
curl http://localhost:8000/settings
```

**Expected response:**
```json
{
  "project_root": "C:\\Users\\gaura\\Downloads\\repo\\myaiagent",
  "model_name": "gemini-2.0-flash-exp",
  "available_models": [
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash",
    "gemini-1.5-pro"
  ]
}
```

**If you get an error:**
- Backend doesn't have the changes
- Restart backend: `uvicorn main:app --reload`

---

## Check Terminal Output

When you run `npm run dev`, you should see:

```
VITE v5.x.x  ready in xxx ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
➜  press h to show help
```

**Watch for:**
- Any errors during build
- Warnings about missing modules
- Port conflicts

---

## Common Issues

### Issue: "Port 3000 is already in use"

**Solution:**
```bash
# Find and kill the process using port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Then restart
npm run dev
```

---

### Issue: Module not found errors

**Solution:**
```bash
# Reinstall dependencies
npm install
npm run dev
```

---

### Issue: TypeScript errors

**Solution:**
```bash
# These are just warnings, the app should still work
# Ignore them for now
```

---

## What You Should See (Screenshots)

### Controls Bar (with Settings button)
```
┌────────────────────────────────────────────────────────────────┐
│ [New Session] [Clear History] [Reload History] [⚙️ Settings]  │
│ [☑ Show Thought Process] [☑ 👔 Dev Lead Review] [☑ ⚡ Streaming]│
└────────────────────────────────────────────────────────────────┘
```

### Settings Panel (after clicking ⚙️ Settings)
```
┌────────────────────────────────────────────────────────────────┐
│ ⚙️ Settings                                                    │
│                                                                │
│ Model Name:                                                    │
│ [gemini-2.0-flash-exp ▼]                                      │
│ Select the Gemini model to use for AI responses               │
│                                                                │
│ Project Root:                                                  │
│ [C:\Users\gaura\Downloads\repo\myaiagent    ] [📁 Browse]     │
│ The root directory where the agent can read/write files       │
│                                                                │
│ [💾 Save Settings] [Cancel]                                   │
└────────────────────────────────────────────────────────────────┘
```

### Textarea Input (multi-line)
```
┌────────────────────────────────────────────────────────────────┐
│ Ask me to help with your code...                              │
│                                                                │
│ Press Shift+Enter to send, Enter for new line.                │
└────────────────────────────────────────────────────────────────┘
                                                          [Send]
```

---

## Quick Checklist

Before asking for help, verify:

- [ ] Ran `npm run dev` and it started successfully
- [ ] Accessing `http://localhost:3000` (correct port)
- [ ] Pressed **Ctrl+Shift+R** to hard refresh
- [ ] Cleared Vite cache (`rmdir /s /q node_modules\.vite`)
- [ ] Tried Incognito/Private mode
- [ ] Backend is running (`curl http://localhost:8000/settings` works)
- [ ] Checked page source for "⚙️ Settings"
- [ ] Checked browser console for errors (F12)

---

## Still Not Working?

### Share This Information:

1. **Terminal output** from `npm run dev`
2. **Browser console errors** (F12 → Console tab)
3. **Network tab** (F12 → Network → refresh page)
4. **Page source** (Right-click → View Page Source, search for "Settings")
5. **Backend response** from `curl http://localhost:8000/settings`

---

## Summary

**The most common issue is browser caching.**

**Quick fix:**
1. Stop frontend (Ctrl+C)
2. Clear cache: `rmdir /s /q node_modules\.vite`
3. Restart: `npm run dev`
4. **Hard refresh browser: Ctrl+Shift+R**

**Keyboard behavior:**
- **Enter** = New line
- **Shift+Enter** = Send message
- **Send button** = Send message

**After following these steps, you WILL see the Settings button and proper textarea behavior!** 🎉
