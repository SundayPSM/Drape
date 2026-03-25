import api from './api'
import type { TokenResponse } from '@/types'

export const authService = {
  async register(email: string, name: string, password: string): Promise<TokenResponse> {
    const { data } = await api.post<TokenResponse>('/api/v1/auth/register', { email, name, password })
    return data
  },

  async login(email: string, password: string): Promise<TokenResponse> {
    const { data } = await api.post<TokenResponse>('/api/v1/auth/login', { email, password })
    return data
  },

  saveTokens(tokens: TokenResponse) {
    localStorage.setItem('access_token', tokens.access_token)
    localStorage.setItem('refresh_token', tokens.refresh_token)
  },

  clearTokens() {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
  },

  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  },
}
