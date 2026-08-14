import http, { httpLong } from './http'
import type { Question, QuestionCreate, Category, Notebook } from '@/types'

export const questionApi = {
  list(params?: { category?: string; status?: string; keyword?: string; notebook_id?: number }) {
    return http.get<unknown, Question[]>('/questions', { params })
  },
  get(id: number) {
    return http.get<unknown, Question>(`/questions/${id}`)
  },
  /** 创建错题会触发 AI 解析（推理模型耗时可达 2-3 分钟），用长超时实例 */
  create(data: QuestionCreate) {
    return httpLong.post<unknown, Question>('/questions', data)
  },
  update(id: number, data: Partial<Question>) {
    return http.put<unknown, Question>(`/questions/${id}`, data)
  },
  /** 重新 AI 分析：返回更新后的完整错题 */
  analyze(id: number) {
    return httpLong.post<unknown, Question>(`/questions/${id}/analyze`)
  },
  remove(id: number) {
    return http.delete<unknown, void>(`/questions/${id}`)
  },
  uploadImage(file: File, notebookId?: number | null) {
    const form = new FormData()
    form.append('file', file)
    if (notebookId) form.append('notebook_id', String(notebookId))
    return httpLong.post<unknown, Question>('/questions/upload', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  /** 只做 OCR 识别（不写入数据库），返回识别文本 + 按「第N题」拆分的片段列表 */
  ocrOnly(file: File) {
    const form = new FormData()
    form.append('file', file)
    return httpLong.post<unknown, { text: string; source: string; questions?: string[] }>('/questions/upload/ocr', form, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  categories() {
    return http.get<unknown, Category[]>('/questions/categories')
  },
  // 错题本（持久化容器）
  notebooks() {
    return http.get<unknown, Notebook[]>('/notebooks')
  },
  createNotebook(name: string) {
    return http.post<unknown, Notebook>('/notebooks', { name })
  },
  deleteNotebook(id: number) {
    return http.delete<unknown, void>(`/notebooks/${id}`)
  }
}
