import axios from 'axios'

const http = axios.create({
  baseURL: '/api',
  timeout: 60000
})

// 针对 AI 相关请求的超时实例：OCR / AI 解析调用推理模型，免费额度下可能耗时 2-3 分钟
export const httpLong = axios.create({
  baseURL: '/api',
  timeout: 240000
})

http.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

httpLong.interceptors.response.use(
  (res) => res.data,
  (err) => {
    const msg = err.response?.data?.detail || err.message || '请求失败'
    return Promise.reject(new Error(msg))
  }
)

export default http
