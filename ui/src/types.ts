// Type definitions for the application

export interface Message {
  role: 'user' | 'assistant' | 'error' | 'status' | 'review'
  content: string
  thought_process?: ThoughtStep[]
  review?: ReviewResult
  timestamp?: string
}

export interface ReviewResult {
  status: string
  review: string
  decision: string
  issues?: string[]
  suggestions?: string[]
  comments?: string[]
}

export interface ThoughtStep {
  action: string
  action_input: string
  observation: string
  reasoning: string
}

export interface QueryResponse {
  status: string
  session_id: string
  response: string
  thought_process?: ThoughtStep[]
  review?: ReviewResult
  message_count: number
}

export interface SessionCreateResponse {
  status: string
  session_id: string
  message: string
}

export interface HistoryResponse {
  status: string
  session_id: string
  messages: Message[]
}

export interface SettingsResponse {
  project_root: string
  model_name: string
  available_models: string[]
}

export interface DirectoryItem {
  name: string
  path: string
  type: string
}

export interface BrowseResponse {
  current_path: string
  parent_path: string | null
  items: DirectoryItem[]
}
