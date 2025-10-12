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

function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [showDetails, setShowDetails] = useState<boolean>(true)
  const [enableReview, setEnableReview] = useState<boolean>(true)
  const [useStreaming, setUseStreaming] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  useEffect(() => {
    createSession()
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
          enable_review: enableReview
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
              setMessages((prev: Message[]) => [...prev, {
                role: 'status' as const,
                content: data.message
              }])
            } else if (data.type === 'step') {
              setMessages((prev: Message[]) => {
                const lastMsg = prev[prev.length - 1]
                if (lastMsg && lastMsg.role === 'status') {
                  return [...prev.slice(0, -1), {
                    role: 'status' as const,
                    content: `${data.action}: ${data.action_input.substring(0, 50)}...`
                  }]
                }
                return prev
              })
            } else if (data.type === 'developer_result') {
              setMessages((prev: Message[]) => {
                const filtered = prev.filter((m: Message) => m.role !== 'status')
                return [...filtered, {
                  role: 'assistant' as const,
                  content: data.response,
                  thought_process: data.thought_process
                }]
              })
            } else if (data.type === 'review') {
              setMessages((prev: Message[]) => [...prev, {
                role: 'review' as const,
                content: data.review.review || 'Review completed',
                review: data.review
              }])
            } else if (data.type === 'complete') {
              // Remove any remaining status messages
              setMessages((prev: Message[]) => prev.filter((m: Message) => m.role !== 'status'))
            } else if (data.type === 'error') {
              setError(data.message)
              setMessages((prev: Message[]) => [...prev, {
                role: 'error' as const,
                content: data.message
              }])
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
          enable_review: enableReview
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

  const newSession = async () => {
    setMessages([])
    setError(null)
    await createSession()
  }

  return (
    <div className="app">
      <header className="header">
        <h1>🤖 Developer Assistant</h1>
        <div className="header-info">
          {sessionId && (
            <span className="session-id">Session: {sessionId.substring(0, 8)}...</span>
          )}
        </div>
      </header>

      <div className="controls">
        <button onClick={newSession} className="btn btn-secondary">
          New Session
        </button>
        <button onClick={clearHistory} className="btn btn-secondary">
          Clear History
        </button>
        <button onClick={loadHistory} className="btn btn-secondary">
          Reload History
        </button>
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
          <span>👔 Dev Lead Review</span>
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

      {error && (
        <div className="error-banner">
          {error}
        </div>
      )}

      <div className="chat-container">
        <div className="messages">
          {messages.length === 0 && (
            <div className="welcome">
              <h2>Welcome to Developer Assistant!</h2>
              <p>I can help you with:</p>
              <ul>
                <li>Creating and editing files</li>
                <li>Reading file contents</li>
                <li>Listing directories</li>
                <li>Deleting files</li>
              </ul>
              <p>Try asking: "Create a Python file with a hello world function"</p>
            </div>
          )}

          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role}`}>
              <div className="message-header">
                <strong>
                  {msg.role === 'user' ? '👤 You' : 
                   msg.role === 'error' ? '❌ Error' : 
                   msg.role === 'status' ? '⚙️ Status' :
                   msg.role === 'review' ? '👔 Dev Lead Review' :
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
          <input
            type="text"
            value={input}
            onChange={(e: ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
            placeholder="Ask me to help with your code..."
            disabled={loading || !sessionId}
            className="input-field"
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
    </div>
  )
}

export default App
