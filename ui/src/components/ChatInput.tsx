import { FormEvent, ChangeEvent } from 'react'
import { FileAttachment } from './FileAttachment'

interface ChatInputProps {
  input: string
  setInput: (input: string) => void
  loading: boolean
  sessionId: string | null
  onSubmit: (e: FormEvent<HTMLFormElement>) => void
  attachedFiles: File[]
  fileInputRef: React.RefObject<HTMLInputElement>
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void
  onRemoveFile: (index: number) => void
  onFileAttach: () => void
}

export function ChatInput({ 
  input, 
  setInput, 
  loading, 
  sessionId, 
  onSubmit,
  attachedFiles,
  fileInputRef,
  onFileChange,
  onRemoveFile,
  onFileAttach
}: ChatInputProps) {
  return (
    <form onSubmit={onSubmit} className="input-form" style={{ flexDirection: 'column', alignItems: 'stretch' }}>
      <FileAttachment
        attachedFiles={attachedFiles}
        fileInputRef={fileInputRef}
        onFileChange={onFileChange}
        onRemoveFile={onRemoveFile}
      />
      
      <div style={{ display: 'flex', gap: '10px', alignItems: 'flex-end' }}>
        <button
          type="button"
          onClick={onFileAttach}
          disabled={loading || !sessionId}
          className="btn-attach"
          title="Attach file"
        >
          📎
        </button>

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
                onSubmit(e as any)
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
      </div>
    </form>
  )
}
