import { useState, useRef, useEffect, FormEvent } from 'react'
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
import { useFileAttachment } from './hooks/useFileAttachment'

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
  const { attachedFiles, fileInputRef, handleFileAttach, handleFileChange, removeFile, readAllFiles, clearFiles } = useFileAttachment()

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Send message handler
  const sendMessage = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!input.trim() || !sessionId) return

    // Read attached files
    const attachedFilesData = await readAllFiles()

    // Create display message - only show filenames, not content
    let displayMessage = input
    if (attachedFilesData.length > 0) {
      displayMessage += '\n\n📎 **Attached Files:** ' + attachedFilesData.map(f => f.filename).join(', ')
    }

    const userMessage: Message = { role: 'user', content: displayMessage }
    setMessages((prev: Message[]) => [...prev, userMessage])
    setInput('')
    clearFiles()
    setLoading(true)
    setError(null)

    try {
      if (useStreaming) {
        await sendMessageStreaming(input, sessionId, showDetails, enableReview, agentType, attachedFilesData)
      } else {
        const data = await apiClient.sendQuery({
          query: input,
          session_id: sessionId,
          show_details: showDetails,
          enable_review: enableReview,
          agent_type: agentType,
          attached_files: attachedFilesData.length > 0 ? attachedFilesData : undefined
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
              attachedFiles={attachedFiles}
              fileInputRef={fileInputRef}
              onFileChange={handleFileChange}
              onRemoveFile={removeFile}
              onFileAttach={handleFileAttach}
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
