import { Message } from '../types'

interface MessageListProps {
  messages: Message[]
  loading: boolean
  showDetails: boolean
}

export function MessageList({ messages, loading, showDetails }: MessageListProps) {
  return (
    <>
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
          <p><strong>☁️ Cloud Architect</strong> provides:</p>
          <ul>
            <li>GCP architecture and design guidance</li>
            <li>Security and compliance recommendations</li>
            <li>Network and infrastructure consulting</li>
            <li>Best practices and optimization advice</li>
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
    </>
  )
}
