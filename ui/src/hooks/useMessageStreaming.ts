import { apiClient } from '../api/apiClient'
import { Message } from '../types'

export function useMessageStreaming(
  setMessages: React.Dispatch<React.SetStateAction<Message[]>>,
  setError: (error: string | null) => void
) {
  const sendMessageStreaming = async (
    query: string,
    sessionId: string,
    showDetails: boolean,
    enableReview: boolean,
    agentType: string,
    attachedFilesData?: Array<{filename: string, content: string}>
  ) => {
    try {
      const response = await apiClient.sendQueryStream({
        query,
        session_id: sessionId,
        show_details: showDetails,
        enable_review: enableReview,
        agent_type: agentType,
        attached_files: attachedFilesData
      })

      if (!response.ok) {
        throw new Error('Stream request failed')
      }

      const reader = response.body?.getReader()
      const decoder = new TextDecoder()

      if (!reader) {
        throw new Error('No reader available')
      }

      let buffer = ''
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) break
        
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''
        
        for (const line of lines) {
          if (!line.trim()) continue
          
          try {
            const data = JSON.parse(line)
            
            if (data.type === 'status') {
              setMessages((prev: Message[]) => {
                const filtered = prev.filter((m: Message) => m.role !== 'status')
                return [...filtered, {
                  role: 'status' as const,
                  content: data.message
                }]
              })
            } else if (data.type === 'step') {
              setMessages((prev: Message[]) => {
                const filtered = prev.filter((m: Message) => m.role !== 'status')
                return [...filtered, {
                  role: 'status' as const,
                  content: `Step ${data.step_number}: ${data.action} - ${data.action_input.substring(0, 80)}...`
                }]
              })
            } else if (data.type === 'developer_result') {
              setMessages((prev: Message[]) => {
                const filtered = prev.filter((m: Message) => m.role !== 'status')
                return [...filtered, {
                  role: 'assistant' as const,
                  content: data.response,
                  thought_process: data.thought_process
                }]
              })
            } else if (data.type === 'review') {
              setMessages((prev: Message[]) => {
                const filtered = prev.filter((m: Message) => m.role !== 'status')
                return [...filtered, {
                  role: 'review' as const,
                  content: data.review.review || 'Review completed',
                  review: data.review
                }]
              })
            } else if (data.type === 'complete') {
              setMessages((prev: Message[]) => prev.filter((m: Message) => m.role !== 'status'))
            } else if (data.type === 'error') {
              setError(data.message)
              setMessages((prev: Message[]) => {
                const filtered = prev.filter((m: Message) => m.role !== 'status')
                return [...filtered, {
                  role: 'error' as const,
                  content: data.message
                }]
              })
            }
          } catch (e) {
            console.error('Failed to parse line:', line, e)
          }
        }
      }
    } catch (err) {
      const error = err as Error
      setError('Streaming error: ' + error.message)
      setMessages(prev => [...prev, {
        role: 'error',
        content: error.message
      }])
    }
  }

  return { sendMessageStreaming }
}
