import { useState } from 'react'
import { AxiosError } from 'axios'
import { apiClient } from '../api/apiClient'
import { DirectoryItem } from '../types'

export function useDirectoryBrowser(setProjectRoot: (path: string) => void) {
  const [showBrowser, setShowBrowser] = useState<boolean>(false)
  const [currentPath, setCurrentPath] = useState<string>('')
  const [parentPath, setParentPath] = useState<string | null>(null)
  const [directories, setDirectories] = useState<DirectoryItem[]>([])
  const [error, setError] = useState<string | null>(null)

  const browseDirectory = async (path?: string) => {
    try {
      const data = await apiClient.browseDirectory(path)
      setCurrentPath(data.current_path)
      setParentPath(data.parent_path)
      setDirectories(data.items)
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

  return {
    showBrowser,
    setShowBrowser,
    currentPath,
    parentPath,
    directories,
    error,
    browseDirectory,
    selectDirectory
  }
}
