import { ChangeEvent } from 'react'

interface SidebarProps {
  agentType: string
  setAgentType: (type: string) => void
  modelName: string
  setModelName: (name: string) => void
  availableModels: string[]
  projectRoot: string
  setProjectRoot: (path: string) => void
  showDetails: boolean
  setShowDetails: (show: boolean) => void
  enableReview: boolean
  setEnableReview: (enable: boolean) => void
  useStreaming: boolean
  setUseStreaming: (use: boolean) => void
  onNewSession: () => void
  onClearHistory: () => void
  onReloadHistory: () => void
  onSaveSettings: () => void
  onBrowseDirectory: () => void
}

export function Sidebar({
  agentType,
  setAgentType,
  modelName,
  setModelName,
  availableModels,
  projectRoot,
  setProjectRoot,
  showDetails,
  setShowDetails,
  enableReview,
  setEnableReview,
  useStreaming,
  setUseStreaming,
  onNewSession,
  onClearHistory,
  onReloadHistory,
  onSaveSettings,
  onBrowseDirectory
}: SidebarProps) {
  return (
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
          <button onClick={onNewSession} className="btn btn-secondary btn-full">
            New Session
          </button>
          <button onClick={onClearHistory} className="btn btn-secondary btn-full">
            Clear History
          </button>
          <button onClick={onReloadHistory} className="btn btn-secondary btn-full">
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
            <button onClick={onBrowseDirectory} className="btn btn-secondary btn-full">
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
          <button onClick={onSaveSettings} className="btn btn-primary btn-full">
            💾 Save Settings
          </button>
        </div>
      </div>
    </aside>
  )
}
