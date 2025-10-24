import { useState, useRef, ChangeEvent } from 'react'

export interface AttachedFileData {
  filename: string
  content: string
}

export function useFileAttachment() {
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileAttach = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const newFiles = Array.from(e.target.files)
      
      // Allow text files, images, and PDFs
      const supportedFiles = newFiles.filter(file => {
        const ext = file.name.split('.').pop()?.toLowerCase()
        const textExtensions = ['txt', 'py', 'js', 'jsx', 'ts', 'tsx', 'json', 'md', 'yaml', 'yml', 'xml', 'html', 'css', 'java', 'c', 'cpp', 'h', 'go', 'rs', 'sh', 'bash', 'sql', 'env', 'config', 'ini', 'toml', 'log']
        const imageExtensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp']
        const pdfExtensions = ['pdf']
        
        const allSupported = [...textExtensions, ...imageExtensions, ...pdfExtensions]
        
        if (!allSupported.includes(ext || '')) {
          alert(`File "${file.name}" is not supported. Supported: text files, images (PNG, JPG, etc.), and PDF`)
          return false
        }
        return true
      })
      
      setAttachedFiles(prev => [...prev, ...supportedFiles])
      
      // Reset the input value to allow re-selecting the same file
      e.target.value = ''
    }
  }

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const readFileContent = async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      const ext = file.name.split('.').pop()?.toLowerCase()
      const binaryExtensions = ['png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'pdf']
      
      reader.onload = (e) => {
        try {
          const result = e.target?.result as string
          // For binary files, we already have base64 from readAsDataURL
          // For text files, we need to convert to base64
          if (binaryExtensions.includes(ext || '')) {
            // Extract base64 data from data URL (remove "data:image/png;base64," prefix)
            const base64Data = result.split(',')[1] || result
            resolve(base64Data)
          } else {
            // Convert text to base64 for consistent backend handling
            const base64Text = btoa(unescape(encodeURIComponent(result)))
            resolve(base64Text)
          }
        } catch (error) {
          reject(new Error(`Failed to encode file ${file.name}: ${error}`))
        }
      }
      reader.onerror = () => reject(new Error(`Failed to read file ${file.name}`))
      
      // Read binary files as base64, text files as text
      if (binaryExtensions.includes(ext || '')) {
        reader.readAsDataURL(file)
      } else {
        reader.readAsText(file)
      }
    })
  }

  const readAllFiles = async (): Promise<AttachedFileData[]> => {
    const filesData: AttachedFileData[] = []
    
    for (const file of attachedFiles) {
      try {
        const content = await readFileContent(file)
        filesData.push({ filename: file.name, content })
      } catch (error) {
        console.error(`Error reading ${file.name}:`, error)
        filesData.push({ 
          filename: file.name, 
          content: `Error reading file: ${error}` 
        })
      }
    }
    
    return filesData
  }

  const clearFiles = () => {
    setAttachedFiles([])
  }

  return {
    attachedFiles,
    fileInputRef,
    handleFileAttach,
    handleFileChange,
    removeFile,
    readAllFiles,
    clearFiles
  }
}
