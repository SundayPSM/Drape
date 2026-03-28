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
    // Listen for Supabase auth state changes (handles page refresh, OAuth callback)
    authService.onAuthStateChange(async (supabaseUser) => {
      if (supabaseUser) {
        try {
          // Fetch our app's user record (created/upserted by backend on first login)
          user.value = await userService.getMe()
        } catch {
          user.value = null
        }
      } else {
        user.value = null
      }
    })

    // Also check current session immediately on app start
    const session = await authService.getSession()
    if (session) {
      try {
        user.value = await userService.getMe()
      } catch {
        user.value = null
      }
    }
  }

  async function loginWithGoogle() {
    loading.value = true
    try {
      await authService.signInWithGoogle()
      // Page will redirect to Google — user.value is set in onAuthStateChange on return
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    await authService.signOut()
    user.value = null
  }

  return { user, loading, isAuthenticated, init, loginWithGoogle, logout }
})
