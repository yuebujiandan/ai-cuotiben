import http from './http'
import type { ChatMessage, AIConversation } from '@/types'

export const chatApi = {
  list() {
    return http.get<unknown, AIConversation[]>('/chat/conversations')
  },
  history(id: number) {
    return http.get<unknown, ChatMessage[]>(`/chat/conversations/${id}/messages`)
  },
  /** 流式对话：通过 fetch 读取 SSE。返回本次会话 ID（新建会话时由后端回传）。 */
  async sendStream(
    question: string,
    context: string,
    onDelta: (text: string) => void,
    conversationId?: number
  ): Promise<number | undefined> {
    const res = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        context,
        conversation_id: conversationId ?? null
      })
    })
    if (!res.ok || !res.body) throw new Error('AI 对话请求失败')

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let full = ''
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      full += decoder.decode(value, { stream: true })
      onDelta(full)
    }
    const convId = res.headers.get('X-Conversation-Id')
    return convId ? Number(convId) : undefined
  },
  analyze(id: number) {
    return http.post<unknown, { analysis: string }>(`/questions/${id}/analyze`)
  },
  /** 3 级讲解：hint(提示) / approach(思路) / solution(详解) */
  explain(question: string, level: 'hint' | 'approach' | 'solution') {
    return http.post<unknown, { level: string; content: string }>('/chat/explain', { question, level })
  }
}
