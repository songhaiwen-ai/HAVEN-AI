import axios from 'axios'

const API_BASE = ''

// 创建带有 JWT Bearer 请求头的 Axios 实例
export const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('haven_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 身份认证 API
export const authApi = {
  login: (username, password) => api.post('/api/v1/auth/login', { username, password }),
  register: (username, password) => api.post('/api/v1/auth/register', { username, password }),
  logout: () => api.post('/api/v1/auth/logout'),
  getMe: () => api.get('/api/v1/auth/me')
}

// 会话管理 API
export const chatApi = {
  getSessions: () => api.get('/api/v1/chat/sessions'),
  createSession: (title) => api.post('/api/v1/chat/sessions', { title }),
  deleteSession: (sessionId) => api.delete(`/api/v1/chat/sessions/${sessionId}`),
  getMessages: (sessionId) => api.get(`/api/v1/chat/sessions/${sessionId}/messages`),
  getArtifact: (sessionId) => api.get(`/api/v1/chat/sessions/${sessionId}/artifact`)
}
