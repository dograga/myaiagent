import { useState, useEffect, useRef, FormEvent, ChangeEvent } from 'react'
import axios, { AxiosError } from 'axios'
import './App.css'

const API_BASE = '/api'

interface Message {
  role: 'user' | 'assistant' | 'error'
  content: string
  thought_process?: ThoughtStep[]
  timestamp?: string
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

  const sendMessage = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    if (!input.trim() || !sessionId) return

    const userMessage: Message = { role: 'user', content: input }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError(null)

    try {
      const response = await axios.post<QueryResponse>(`${API_BASE}/query`, {
        query: input,
        session_id: sessionId,
        show_details: showDetails
      })

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.data.response,
        thought_process: response.data.thought_process
      }

      setMessages(prev => [...prev, assistantMessage])
    } catch (err) {
      const error = err as AxiosError<{ detail: string }>
      const errorMessage = error.response?.data?.detail || error.message
      setError('Error: ' + errorMessage)
      setMessages(prev => [...prev, {
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
                <strong>{msg.role === 'user' ? '👤 You' : msg.role === 'error' ? '❌ Error' : '🤖 Assistant'}</strong>
              </div>
              <div className="message-content">
                {msg.content}
              </div>
              
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
