import { DirectoryItem } from '../types'

interface DirectoryBrowserProps {
  currentPath: string
  parentPath: string | null
  directories: DirectoryItem[]
  onBrowse: (path: string) => void
  onSelect: (path: string) => void
  onClose: () => void
}

export function DirectoryBrowser({
  currentPath,
  parentPath,
  directories,
  onBrowse,
  onSelect,
  onClose
}: DirectoryBrowserProps) {
  return (
    <div className="directory-browser">
      <div className="browser-header">
        <h3>📁 Browse Directory</h3>
        <button onClick={onClose} className="btn-close">✕</button>
      </div>
      
      <div className="current-path">
        <strong>Current:</strong> {currentPath}
      </div>

      <div className="directory-list">
        {parentPath && (
          <div 
            className="directory-item parent" 
            onClick={() => onBrowse(parentPath)}
          >
            <span>📁 ..</span>
          </div>
        )}
        
        {directories.map((dir) => (
          <div 
            key={dir.path} 
            className="directory-item"
          >
            <span onClick={() => onBrowse(dir.path)} style={{ cursor: 'pointer', flex: 1 }}>
              📁 {dir.name}
            </span>
            <button 
              onClick={(e) => {
                e.stopPropagation()
                onSelect(dir.path)
              }}
              className="btn btn-small"
            >
              Select
            </button>
          </div>
        ))}
      </div>

      <div className="browser-actions">
        <button onClick={() => onSelect(currentPath)} className="btn btn-primary">
          Select Current Directory
        </button>
      </div>
    </div>
  )
}
