import { useState, useEffect, useRef, FormEvent, ChangeEvent } from 'react'
import axios, { AxiosError } from 'axios'
import './App.css'

const API_BASE = '/api'

interface Message {
  role: 'user' | 'assistant' | 'error' | 'status' | 'review'
  content: string
  thought_process?: ThoughtStep[]
  review?: ReviewResult
  timestamp?: string
}

interface ReviewResult {
  status: string
  review: string
  decision: string
  issues?: string[]
  suggestions?: string[]
  comments?: string[]
}

interface ThoughtStep {
  action: string
  action_input: string
  observation: string
  reasoning: string
}

interface QueryResponse {
  status: string
  session_id: string
  response: string
  thought_process?: ThoughtStep[]
  review?: ReviewResult
  message_count: number
}

interface SessionCreateResponse {
  status: string
  session_id: string
  message: string
}

interface HistoryResponse {
  status: string
  session_id: string
  messages: Message[]
}

interface SettingsResponse {
  project_root: string
  model_name: string
  available_models: string[]
}

interface DirectoryItem {
  name: string
  path: string
  type: string
}

interface BrowseResponse {
  current_path: string
  parent_path: string | null
  items: DirectoryItem[]
}

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [showDetails, setShowDetails] = useState<boolean>(true)
  const [enableReview, setEnableReview] = useState<boolean>(true)
  const [useStreaming, setUseStreaming] = useState<boolean>(true)
  const [agentType, setAgentType] = useState<string>('developer')
  const [error, setError] = useState<string | null>(null)
  const [projectRoot, setProjectRoot] = useState<string>('')
  const [modelName, setModelName] = useState<string>('gemini-2.5-flash')
  const [availableModels, setAvailableModels] = useState<string[]>([
    'gemini-2.5-flash',
    'gemini-2.5-pro'
  ])
  const [showBrowser, setShowBrowser] = useState<boolean>(false)
  const [currentPath, setCurrentPath] = useState<string>('')
  const [parentPath, setParentPath] = useState<string | null>(null)
  const [directories, setDirectories] = useState<DirectoryItem[]>([])
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    createSession()
    loadSettings()
  }, [])

  const createSession = async () => {
    try {
      const response = await axios.post<SessionCreateResponse>(`${API_BASE}/session/create`)
      setSessionId(response.data.session_id)
      setError(null)
    } catch (err) {
      const error = err as AxiosError
      setError('Failed to create session: ' + error.message)
    }
  }

  const loadHistory = async () => {
    if (!sessionId) return
    try {
      const response = await axios.get<HistoryResponse>(`${API_BASE}/session/${sessionId}/history`)
      const history = response.data.messages
      setMessages(history)
    } catch (err) {
      console.error('Failed to load history:', err)
    }
  }

  const sendMessageStreaming = async (query: string) => {
    try {
      const response = await fetch(`${API_BASE}/query/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query,
          session_id: sessionId,
          show_details: showDetails,
          enable_review: enableReview,
          agent_type: agentType
        })
      })

      if (!response.ok) {
        throw new Error('Stream request failed')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No reader available')
      }

      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (!line.trim()) continue
          
          try {
            const data = JSON.parse(line)
            
            if (data.type === 'status') {
              // Add or update status message
              setMessages((prev: Message[]) => {
                // Remove previous status messages and add new one
                const filtered = prev.filter((m: Message) => m.role !== 'status')
                return [...filtered, {
                  role: 'status' as const,
                  content: data.message
                }]
              })
            } else if (data.type === 'step') {
              // Show each step as it happens
              setMessages((prev: Message[]) => {
                const filtered = prev.filter((m: Message) => m.role !== 'status')
                return [...filtered, {
                  role: 'status' as const,
                  content: `Step ${data.step_number}: ${data.action} - ${data.action_input.substring(0, 80)}...`
                }]
              })
            } else if (data.type === 'developer_result') {
              // Remove status messages and show final result
              setMessages((prev: Message[]) => {
                const filtered = prev.filter((m: Message) => m.role !== 'status')
                return [...filtered, {
                  role: 'assistant' as const,
                  content: data.response,
                  thought_process: data.thought_process
                }]
              })
            } else if (data.type === 'review') {
              // Remove status messages and add review
              setMessages((prev: Message[]) => {
                const filtered = prev.filter((m: Message) => m.role !== 'status')
                return [...filtered, {
                  role: 'review' as const,
                  content: data.review.review || 'Review completed',
                  review: data.review
                }]
              })
            } else if (data.type === 'complete') {
              // Remove any remaining status messages
              setMessages((prev: Message[]) => prev.filter((m: Message) => m.role !== 'status'))
            } else if (data.type === 'error') {
              setError(data.message)
              setMessages((prev: Message[]) => {
                const filtered = prev.filter((m: Message) => m.role !== 'status')
                return [...filtered, {
                  role: 'error' as const,
                  content: data.message
                }]
              })
            }
          } catch (e) {
            console.error('Failed to parse line:', line, e)
          }
        }
      }
    } catch (err) {
      const error = err as Error
      setError('Streaming error: ' + error.message)
      setMessages(prev => [...prev, {
        role: 'error',
        content: error.message
      }])
    }
  }

  const sendMessage = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!input.trim() || !sessionId) return

    const userMessage: Message = { role: 'user', content: input }
    const query = input
    setMessages((prev: Message[]) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      if (useStreaming) {
        await sendMessageStreaming(query)
      } else {
        const response = await axios.post<QueryResponse>(`${API_BASE}/query`, {
          query,
          session_id: sessionId,
          show_details: showDetails,
          enable_review: enableReview,
          agent_type: agentType
        })

        const assistantMessage: Message = {
          role: 'assistant',
          content: response.data.response,
          thought_process: response.data.thought_process,
          review: response.data.review
        }

        setMessages((prev: Message[]) => [...prev, assistantMessage])
        
        if (response.data.review) {
          setMessages((prev: Message[]) => [...prev, {
            role: 'review',
            content: response.data.review?.review || 'Review completed',
            review: response.data.review
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

  const clearHistory = async () => {
    if (!sessionId) return
    try {
      await axios.post(`${API_BASE}/session/${sessionId}/clear`)
      setMessages([])
      setError(null)
    } catch (err) {
      const error = err as AxiosError
      setError('Failed to clear history: ' + error.message)
    }
  }

  const loadSettings = async () => {
    try {
      const response = await axios.get<SettingsResponse>(`${API_BASE}/settings`)
      setProjectRoot(response.data.project_root)
      setModelName(response.data.model_name)
      setAvailableModels(response.data.available_models)
    } catch (err) {
      console.error('Failed to load settings:', err)
    }
  }

  const saveSettings = async () => {
    try {
      await axios.post(`${API_BASE}/settings`, {
        project_root: projectRoot,
        model_name: modelName
      })
      setError(null)
      alert('Settings saved successfully! Agents have been reinitialized.')
    } catch (err) {
      const error = err as AxiosError<{ detail: string }>
      setError('Failed to save settings: ' + (error.response?.data?.detail || error.message))
    }
  }

  const browseDirectory = async (path?: string) => {
    try {
      const url = path ? `${API_BASE}/browse-directory?path=${encodeURIComponent(path)}` : `${API_BASE}/browse-directory`
      const response = await axios.get<BrowseResponse>(url)
      setCurrentPath(response.data.current_path)
      setParentPath(response.data.parent_path)
      setDirectories(response.data.items)
      setShowBrowser(true)
    } catch (err) {
      const error = err as AxiosError<{ detail: string }>
      setError('Failed to browse directory: ' + (error.response?.data?.detail || error.message))
    }
  }

  const selectDirectory = (path: string) => {
    setProjectRoot(path)
    setShowBrowser(false)
  }

  const newSession = async () => {
    setMessages([])
    setError(null)
    await createSession()
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 AI Assistant</h1>
        <div className="header-info">
          {sessionId && (
            <span className="session-id">Session: {sessionId.substring(0, 8)}...</span>
          )}
        </div>
      </header>

      <div className="main-layout">
        {/* Left Sidebar - Session & Settings */}
        <aside className="sidebar">
          <div className="sidebar-section">
            <h3>🤖 Agent Type</h3>
            <div className="setting-group">
              <select 
                value={agentType} 
                onChange={(e: ChangeEvent<HTMLSelectElement>) => setAgentType(e.target.value)}
                className="setting-select"
              >
                <option value="developer">👨‍💻 Developer Agent</option>
                <option value="devops">🔧 DevOps Agent</option>
                <option value="cloud_architect">☁️ Cloud Architect</option>
              </select>
              <small>Choose between Developer, DevOps, or Cloud Architect expertise</small>
            </div>
          </div>

          <div className="sidebar-section">
            <h3>📋 Session</h3>
            <div className="sidebar-buttons">
              <button onClick={newSession} className="btn btn-secondary btn-full">
                New Session
              </button>
              <button onClick={clearHistory} className="btn btn-secondary btn-full">
                Clear History
              </button>
              <button onClick={loadHistory} className="btn btn-secondary btn-full">
                Reload History
              </button>
            </div>
          </div>

          <div className="sidebar-section">
            <h3>⚙️ Settings</h3>
            
            <div className="setting-group">
              <label>Model:</label>
              <select 
                value={modelName} 
                onChange={(e) => setModelName(e.target.value)}
                className="setting-select"
              >
                {availableModels.map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
            </div>

            <div className="setting-group">
              <label>Project Root:</label>
              <div className="current-project-root">
                <code>{projectRoot || 'Not set'}</code>
              </div>
              <div className="path-input-group-vertical">
                <input 
                  type="text" 
                  value={projectRoot} 
                  onChange={(e) => setProjectRoot(e.target.value)}
                  className="setting-input"
                  placeholder="/path/to/project"
                />
                <button onClick={() => browseDirectory()} className="btn btn-secondary btn-full">
                  📁 Browse
                </button>
              </div>
            </div>

            <div className="sidebar-toggles">
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={showDetails}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setShowDetails(e.target.checked)}
                />
                <span>Show Thought Process</span>
              </label>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={enableReview}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setEnableReview(e.target.checked)}
                />
                <span>👔 Lead Review</span>
              </label>
              <label className="toggle">
                <input
                  type="checkbox"
                  checked={useStreaming}
                  onChange={(e: ChangeEvent<HTMLInputElement>) => setUseStreaming(e.target.checked)}
                />
                <span>⚡ Streaming</span>
              </label>
            </div>

            <div className="setting-actions">
              <button onClick={saveSettings} className="btn btn-primary btn-full">
                💾 Save Settings
              </button>
            </div>
          </div>
        </aside>

        {/* Right Main Area - Chat */}
        <main className="main-content">
          {error && (
            <div className="error-banner">
              {error}
            </div>
          )}

          <div className="chat-container">
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <h2>Welcome to AI Assistant!</h2>
              <p><strong>👨‍💻 Developer Agent</strong> can help you with:</p>
              <ul>
                <li>Creating and editing code files</li>
                <li>Reading and modifying file contents</li>
                <li>Python, JavaScript, and other programming languages</li>
                <li>Code reviews and best practices</li>
              </ul>
              <p><strong>🔧 DevOps Agent</strong> specializes in:</p>
              <ul>
                <li>Terraform infrastructure as code</li>
                <li>Kubernetes deployments and configurations</li>
                <li>Jenkins CI/CD pipelines</li>
                <li>Groovy scripting and automation</li>
              </ul>
              <p>Try asking: "Create a Python file with a hello world function" or "Help me set up a Kubernetes deployment"</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-header">
                <strong>
                  {msg.role === 'user' ? '👤 You' : 
                    msg.role === 'error' ? '❌ Error' : 
                    msg.role === 'status' ? '⚙️ Status' :
                    msg.role === 'review' ? '👔 Lead Review' :
                    '🤖 Assistant'}
                </strong>
              </div>
              <div className="message-content">
                {msg.content}
              </div>
              
              {msg.review && (
                <div className="review-details">
                  <div className={`review-decision ${msg.review.decision}`}>
                    <strong>Decision:</strong> {msg.review.decision.toUpperCase()}
                  </div>
                  {msg.review.issues && msg.review.issues.length > 0 && (
                    <div className="review-issues">
                      <strong>Issues:</strong>
                      <ul>
                        {msg.review.issues.map((issue, i) => (
                          <li key={i}>{issue}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {msg.review.suggestions && msg.review.suggestions.length > 0 && (
                    <div className="review-suggestions">
                      <strong>Suggestions:</strong>
                      <ul>
                        {msg.review.suggestions.map((suggestion, i) => (
                          <li key={i}>{suggestion}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {msg.review.comments && msg.review.comments.length > 0 && (
                    <div className="review-comments">
                      <strong>Comments:</strong>
                      <ul>
                        {msg.review.comments.map((comment, i) => (
                          <li key={i}>{comment}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
              
              {msg.thought_process && showDetails && (
                <details className="thought-process">
                  <summary>🧠 Thought Process ({msg.thought_process.length} steps)</summary>
                  {msg.thought_process.map((step, i) => (
                    <div key={i} className="thought-step">
                      <div className="step-header">Step {i + 1}: {step.action}</div>
                      <div className="step-input">
                        <strong>Input:</strong>
                        <pre><code>{step.action_input}</code></pre>
                      </div>
                      <div className="step-observation">
                        <strong>Result:</strong>
                        <pre><code>{step.observation}</code></pre>
                      </div>
                    </div>
                  ))}
                </details>
              )}
            </div>
          ))}

          {loading && (
            <div className="message assistant">
              <div className="message-header">
                <strong>🤖 Assistant</strong>
              </div>
              <div className="message-content loading">
                <span className="dot">.</span>
                <span className="dot">.</span>
                <span className="dot">.</span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        <form onSubmit={sendMessage} className="input-form">
          <textarea
            value={input}
            onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setInput(e.target.value)}
            placeholder="Ask me to help with your code...\n\nPress Shift+Enter to send, Enter for new line."
            disabled={loading || !sessionId}
            className="input-field"
            rows={3}
            onKeyDown={(e) => {
              // Submit on Shift+Enter (Enter alone = new line)
              if (e.key === 'Enter' && e.shiftKey) {
                e.preventDefault()
                if (!loading && sessionId && input.trim()) {
                  sendMessage(e as any)
                }
              }
            }}
          />
          <button 
            type="submit" 
            disabled={loading || !sessionId || !input.trim()}
            className="btn btn-primary"
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </form>
          </div>
        </main>
      </div>

      {showBrowser && (
        <div className="directory-browser">
          <div className="browser-header">
            <h3>📁 Browse Directory</h3>
            <button onClick={() => setShowBrowser(false)} className="btn-close">✕</button>
          </div>
          
          <div className="current-path">
            <strong>Current:</strong> {currentPath}
          </div>

          <div className="directory-list">
            {parentPath && (
              <div 
                className="directory-item parent" 
                onClick={() => browseDirectory(parentPath)}
              >
                <span>📁 ..</span>
              </div>
            )}
            
            {directories.map((dir) => (
              <div 
                key={dir.path} 
                className="directory-item"
              >
                <span onClick={() => browseDirectory(dir.path)} style={{ cursor: 'pointer', flex: 1 }}>📁 {dir.name}</span>
                <button 
                  onClick={(e) => {
                    e.stopPropagation()
                    selectDirectory(dir.path)
                  }}
                  className="btn btn-small"
                >
                  Select
                </button>
              </div>
            ))}
          </div>

          <div className="browser-actions">
            <button onClick={() => selectDirectory(currentPath)} className="btn btn-primary">
              Select Current Directory
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default App