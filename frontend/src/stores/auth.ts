import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authService } from '@/services/auth.service'
import { userService } from '@/services/user.service'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!user.value)

  async function init() {
    if (authService.isAuthenticated()) {
      try {
        user.value = await userService.getMe()
      } catch {
        authService.clearTokens()
      }
    }
  }

  async function register(email: string, name: string, password: string) {
    loading.value = true
    try {
      const tokens = await authService.register(email, name, password)
      authService.saveTokens(tokens)
      user.value = await userService.getMe()
    } finally {
      loading.value = false
    }
  }

  async function login(email: string, password: string) {
    loading.value = true
    try {
      const tokens = await authService.login(email, password)
      authService.saveTokens(tokens)
      user.value = await userService.getMe()
    } finally {
      loading.value = false
    }
  }

  function logout() {
    authService.clearTokens()
    user.value = null
  }

  return { user, loading, isAuthenticated, init, register, login, logout }
})
