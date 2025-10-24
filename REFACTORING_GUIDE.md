# App.tsx Refactoring Guide

## Overview

I've created a modular structure to make `App.tsx` much cleaner and more maintainable. The original 670-line file can be reduced to ~150 lines by extracting components, hooks, and utilities.

## New File Structure

```
ui/src/
├── types.ts                          # All TypeScript interfaces
├── api/
│   └── apiClient.ts                  # All API calls centralized
├── components/
│   ├── Sidebar.tsx                   # Left sidebar with settings
│   ├── MessageList.tsx               # Message display component
│   ├── ChatInput.tsx                 # Input form component
│   └── DirectoryBrowser.tsx          # Directory browser modal
├── hooks/
│   ├── useSession.ts                 # Session management logic
│   ├── useSettings.ts                # Settings management logic
│   ├── useDirectoryBrowser.ts        # Directory browsing logic
│   └── useMessageStreaming.ts        # Streaming message logic
└── App.tsx                           # Main component (simplified)
```

## What Each Module Does

### 1. `types.ts` (67 lines)
- All TypeScript interfaces and types
- No logic, just type definitions
- Imported by other modules

### 2. `api/apiClient.ts` (75 lines)
- Centralized API client
- All axios/fetch calls in one place
- Easy to mock for testing
- Functions: `createSession`, `loadHistory`, `sendQuery`, `sendQueryStream`, `loadSettings`, `saveSettings`, `browseDirectory`

### 3. `components/Sidebar.tsx` (149 lines)
- Entire left sidebar
- Agent selection, session controls, settings
- Pure presentational component
- Takes props and callbacks

### 4. `components/MessageList.tsx` (128 lines)
- Displays all messages
- Welcome screen
- Review details
- Thought process
- Loading indicator

### 5. `components/ChatInput.tsx` (42 lines)
- Simple input form
- Textarea and send button
- Keyboard shortcuts
- Can be extended for file attachment

### 6. `components/DirectoryBrowser.tsx` (68 lines)
- Directory browsing modal
- Separate from main UI
- Reusable component

### 7. `hooks/useSession.ts` (62 lines)
- Session state management
- Create, load, clear session
- Message state
- Error handling

### 8. `hooks/useSettings.ts` (49 lines)
- Settings state management
- Load and save settings
- Model and project root

### 9. `hooks/useDirectoryBrowser.ts` (40 lines)
- Directory browser state
- Browse and select logic

### 10. `hooks/useMessageStreaming.ts` (125 lines)
- Streaming message logic
- All streaming parsing
- Message updates

## Benefits

### ✅ Maintainability
- Each file has a single responsibility
- Easy to find and fix bugs
- Clear separation of concerns

### ✅ Testability
- Each module can be tested independently
- API client can be mocked
- Components can be tested in isolation

### ✅ Reusability
- Components can be reused in other parts of the app
- Hooks can be shared across components
- API client can be used anywhere

### ✅ Readability
- Main App.tsx becomes ~150 lines instead of 670
- Each file is focused and understandable
- Clear imports show dependencies

### ✅ Scalability
- Easy to add new features
- Easy to add new components
- Easy to add new API endpoints

## Simplified App.tsx Structure

After refactoring, App.tsx would look like:

```typescript
import { useState, useRef, useEffect } from 'react'
import { AxiosError } from 'axios'
import './App.css'

// Import types
import { Message } from './types'

// Import API client
import { apiClient } from './api/apiClient'

// Import components
import { Sidebar } from './components/Sidebar'
import { MessageList } from './components/MessageList'
import { ChatInput } from './components/ChatInput'
import { DirectoryBrowser } from './components/DirectoryBrowser'

// Import hooks
import { useSession } from './hooks/useSession'
import { useSettings } from './hooks/useSettings'
import { useDirectoryBrowser } from './hooks/useDirectoryBrowser'
import { useMessageStreaming } from './hooks/useMessageStreaming'

function App() {
  // UI state
  const [input, setInput] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [showDetails, setShowDetails] = useState<boolean>(true)
  const [enableReview, setEnableReview] = useState<boolean>(true)
  const [useStreaming, setUseStreaming] = useState<boolean>(true)
  const [agentType, setAgentType] = useState<string>('developer')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Custom hooks
  const { sessionId, messages, setMessages, error, setError, loadHistory, clearHistory, newSession } = useSession()
  const { projectRoot, setProjectRoot, modelName, setModelName, availableModels, saveSettings } = useSettings()
  const { showBrowser, setShowBrowser, currentPath, parentPath, directories, browseDirectory, selectDirectory } = useDirectoryBrowser(setProjectRoot)
  const { sendMessageStreaming } = useMessageStreaming(setMessages, setError)

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Send message handler
  const sendMessage = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!input.trim() || !sessionId) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages((prev: Message[]) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      if (useStreaming) {
        await sendMessageStreaming(input, sessionId, showDetails, enableReview, agentType)
      } else {
        const data = await apiClient.sendQuery({
          query: input,
          session_id: sessionId,
          show_details: showDetails,
          enable_review: enableReview,
          agent_type: agentType
        })

        const assistantMessage: Message = {
          role: 'assistant',
          content: data.response,
          thought_process: data.thought_process,
          review: data.review
        }

        setMessages((prev: Message[]) => [...prev, assistantMessage])
        
        if (data.review) {
          setMessages((prev: Message[]) => [...prev, {
            role: 'review',
            content: data.review?.review || 'Review completed',
            review: data.review
          }])
        }
      }
    } catch (err) {
      const error = err as AxiosError<{ detail: string }>
      const errorMessage = error.response?.data?.detail || error.message
      setError('Error: ' + errorMessage)
      setMessages((prev: Message[]) => [...prev, {
        role: 'error',
        content: errorMessage
      }])
    } finally {
      setLoading(false)
    }
  }

  const handleSaveSettings = async () => {
    try {
      await saveSettings()
      setError(null)
    } catch (err) {
      setError((err as Error).message)
    }
  }

  return (
    <div className="app">
      <div className="main-layout">
        <Sidebar
          agentType={agentType}
          setAgentType={setAgentType}
          modelName={modelName}
          setModelName={setModelName}
          availableModels={availableModels}
          projectRoot={projectRoot}
          setProjectRoot={setProjectRoot}
          showDetails={showDetails}
          setShowDetails={setShowDetails}
          enableReview={enableReview}
          setEnableReview={setEnableReview}
          useStreaming={useStreaming}
          setUseStreaming={setUseStreaming}
          onNewSession={newSession}
          onClearHistory={clearHistory}
          onReloadHistory={loadHistory}
          onSaveSettings={handleSaveSettings}
          onBrowseDirectory={() => browseDirectory()}
        />

        <main className="main-content">
          {error && <div className="error-banner">{error}</div>}

          <div className="chat-container">
            <div className="messages">
              <MessageList messages={messages} loading={loading} showDetails={showDetails} />
              <div ref={messagesEndRef} />
            </div>

            <ChatInput
              input={input}
              setInput={setInput}
              loading={loading}
              sessionId={sessionId}
              onSubmit={sendMessage}
            />
          </div>
        </main>
      </div>

      {showBrowser && (
        <DirectoryBrowser
          currentPath={currentPath}
          parentPath={parentPath}
          directories={directories}
          onBrowse={browseDirectory}
          onSelect={selectDirectory}
          onClose={() => setShowBrowser(false)}
        />
      )}
    </div>
  )
}

export default App
```

## Migration Steps

### Step 1: Create New Files
1. Create all the new files listed above
2. Copy the code from the modules I created

### Step 2: Update App.tsx
1. Backup current App.tsx
2. Replace with the simplified version above
3. Test each feature one by one

### Step 3: Test
1. Test session creation
2. Test message sending
3. Test settings
4. Test directory browser
5. Test streaming

### Step 4: Add File Attachment
Once the refactoring is done, adding file attachment becomes much easier:
1. Create `components/FileAttachment.tsx`
2. Create `hooks/useFileAttachment.ts`
3. Import and use in App.tsx
4. Much cleaner than modifying the monolithic file!

## Future Enhancements

With this structure, you can easily add:
- `components/FileAttachment.tsx` - File upload UI
- `hooks/useFileAttachment.ts` - File handling logic
- `utils/fileReader.ts` - File reading utilities
- `components/MessageInput.tsx` - Enhanced input with file support
- `api/fileUpload.ts` - File upload API calls

## Summary

**Before:** 670 lines in one file
**After:** ~150 lines in App.tsx + 10 focused modules

This makes the codebase:
- ✅ Easier to understand
- ✅ Easier to maintain
- ✅ Easier to test
- ✅ Easier to extend
- ✅ More professional

Would you like me to create the simplified App.tsx file that uses all these modules?
