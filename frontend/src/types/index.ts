/** 错题状态：green=已掌握 / amber=待复习 / red=未掌握 */
export type QuestionStatus = 'green' | 'amber' | 'red'

export interface Question {
  id: number
  subject: string
  knowledge_point: string
  source: string
  content: string
  my_answer?: string
  correct_answer?: string
  ai_analysis?: string
  status: QuestionStatus
  review_count: number
  is_favorite: boolean
  notebook_id?: number | null
  created_at: string
}

export interface Notebook {
  id: number
  name: string
  created_at: string
  count: number
}

export interface QuestionCreate {
  content: string
  my_answer?: string
  subject?: string
  knowledge_point?: string
  notebook_id?: number | null
  source?: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface DashboardStats {
  total: number
  mastered: number
  reviewing: number
  pending: number
  mastery_rate: number
  review_today: number
  streak_days: number
}

export interface DailyStat {
  date: string
  total: number
  correct: number
  review: number
}

export interface AIConversation {
  id: number
  title: string
  created_at: string
}

export interface Category {
  name: string
  count: number
}
