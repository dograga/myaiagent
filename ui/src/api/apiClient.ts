// API client for backend communication
import axios from 'axios'
import {
  SessionCreateResponse,
  HistoryResponse,
  QueryResponse,
  SettingsResponse,
  BrowseResponse
} from '../types'

const API_BASE = '/api'

export const apiClient = {
  // Session management
  createSession: async () => {
    const response = await axios.post<SessionCreateResponse>(`${API_BASE}/session/create`)
    return response.data
  },

  loadHistory: async (sessionId: string) => {
    const response = await axios.get<HistoryResponse>(`${API_BASE}/session/${sessionId}/history`)
    return response.data
  },

  clearHistory: async (sessionId: string) => {
    await axios.post(`${API_BASE}/session/${sessionId}/clear`)
  },

  // Query endpoints
  sendQuery: async (data: {
    query: string
    session_id: string
    show_details: boolean
    enable_review: boolean
    agent_type: string
    attached_files?: Array<{filename: string, content: string}>
  }) => {
    const response = await axios.post<QueryResponse>(`${API_BASE}/query`, data)
    return response.data
  },

  sendQueryStream: async (data: {
    query: string
    session_id: string
    show_details: boolean
    enable_review: boolean
    agent_type: string
    attached_files?: Array<{filename: string, content: string}>
  }) => {
    return fetch(`${API_BASE}/query/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data)
    })
  },

  // Settings
  loadSettings: async () => {
    const response = await axios.get<SettingsResponse>(`${API_BASE}/settings`)
    return response.data
  },

  saveSettings: async (data: { project_root?: string, model_name?: string }) => {
    await axios.post(`${API_BASE}/settings`, data)
  },

  // Directory browsing
  browseDirectory: async (path?: string) => {
    const url = path 
      ? `${API_BASE}/browse-directory?path=${encodeURIComponent(path)}` 
      : `${API_BASE}/browse-directory`
    const response = await axios.get<BrowseResponse>(url)
    return response.data
  }
}
