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
      setAttachedFiles(prev => [...prev, ...newFiles])
    }
  }

  const removeFile = (index: number) => {
    setAttachedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const readFileContent = async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => resolve(e.target?.result as string)
      reader.onerror = reject
      reader.readAsText(file)
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
