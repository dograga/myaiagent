import { useState, useEffect } from 'react'
import { AxiosError } from 'axios'
import { apiClient } from '../api/apiClient'
import { Message } from '../types'

export function useSession() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    createSession()
  }, [])

  const createSession = async () => {
    try {
      const data = await apiClient.createSession()
      setSessionId(data.session_id)
      setError(null)
    } catch (err) {
      const error = err as AxiosError
      setError('Failed to create session: ' + error.message)
    }
  }

  const loadHistory = async () => {
    if (!sessionId) return
    try {
      const data = await apiClient.loadHistory(sessionId)
      setMessages(data.messages)
    } catch (err) {
      console.error('Failed to load history:', err)
    }
  }

  const clearHistory = async () => {
    if (!sessionId) return
    try {
      await apiClient.clearHistory(sessionId)
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

  return {
    sessionId,
    messages,
    setMessages,
    error,
    setError,
    loadHistory,
    clearHistory,
    newSession
  }
}
