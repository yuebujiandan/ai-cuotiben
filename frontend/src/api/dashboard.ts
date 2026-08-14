import http from './http'
import type { DashboardStats, DailyStat } from '@/types'

export const dashboardApi = {
  stats() {
    return http.get<unknown, DashboardStats>('/dashboard/stats')
  },
  daily() {
    return http.get<unknown, DailyStat[]>('/dashboard/daily')
  },
  exportPdf() {
    return http.get<unknown, { url: string }>('/dashboard/export')
  }
}
