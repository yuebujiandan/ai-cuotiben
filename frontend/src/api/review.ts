import http from './http'
import type { Question } from '@/types'

export const reviewApi = {
  /** 今日复习队列（未掌握优先，上限 30） */
  queue() {
    return http.get<unknown, Question[]>('/review/queue')
  },
  /** 提交作答结果：correct / wrong / skip */
  submit(id: number, result: 'correct' | 'wrong' | 'skip') {
    return http.post<unknown, Question>(`/review/${id}/result`, { result })
  }
}
