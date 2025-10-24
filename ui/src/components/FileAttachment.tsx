import { ChangeEvent } from 'react'

interface FileAttachmentProps {
  attachedFiles: File[]
  fileInputRef: React.RefObject<HTMLInputElement>
  onFileChange: (e: ChangeEvent<HTMLInputElement>) => void
  onRemoveFile: (index: number) => void
}

export function FileAttachment({
  attachedFiles,
  fileInputRef,
  onFileChange,
  onRemoveFile
}: FileAttachmentProps) {
  return (
    <>
      <input
        type="file"
        ref={fileInputRef}
        onChange={onFileChange}
        style={{ display: 'none' }}
        multiple
      />
      
      {attachedFiles.length > 0 && (
        <div className="attached-files">
          {attachedFiles.map((file, index) => (
            <div key={index} className="attached-file">
              <span>📎 {file.name}</span>
              <button
                type="button"
                onClick={() => onRemoveFile(index)}
                className="remove-file-btn"
                title="Remove file"
              >
                ✕
              </button>
            </div>
          ))}
        </div>
      )}
    </>
  )
}
