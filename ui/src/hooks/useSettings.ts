import { useState, useEffect } from 'react'
import { AxiosError } from 'axios'
import { apiClient } from '../api/apiClient'

export function useSettings() {
  const [projectRoot, setProjectRoot] = useState<string>('')
  const [modelName, setModelName] = useState<string>('gemini-2.5-flash')
  const [availableModels, setAvailableModels] = useState<string[]>([
    'gemini-2.5-pro',
    'gemini-2.5-flash'
  ])

  useEffect(() => {
    loadSettings()
  }, [])

  const loadSettings = async () => {
    try {
      const data = await apiClient.loadSettings()
      setProjectRoot(data.project_root)
      setModelName(data.model_name)
      setAvailableModels(data.available_models)
    } catch (err) {
      console.error('Failed to load settings:', err)
    }
  }

  const saveSettings = async () => {
    try {
      await apiClient.saveSettings({
        project_root: projectRoot,
        model_name: modelName
      })
      alert('Settings saved successfully! Agents have been reinitialized.')
    } catch (err) {
      const error = err as AxiosError<{ detail: string }>
      throw new Error('Failed to save settings: ' + (error.response?.data?.detail || error.message))
    }
  }

  return {
    projectRoot,
    setProjectRoot,
    modelName,
    setModelName,
    availableModels,
    saveSettings
  }
}
