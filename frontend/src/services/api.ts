import axios, { type AxiosError } from 'axios'
import { supabase } from './supabase'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  headers: { 'Content-Type': 'application/json' },
  timeout: 30000,
})

// Attach Supabase access token to every request
api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// On 401 try to refresh the Supabase session once, then redirect to login
api.interceptors.response.use(
  (res) => res,
  async (error: AxiosError) => {
    const original = error.config as any
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const { data, error: refreshError } = await supabase.auth.refreshSession()
      if (!refreshError && data.session) {
        original.headers.Authorization = `Bearer ${data.session.access_token}`
        return api(original)
      }
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

export default api
