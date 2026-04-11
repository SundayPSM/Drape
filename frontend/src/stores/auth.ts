import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { supabase } from '@/services/supabase'
import { authService } from '@/services/auth.service'
import { userService } from '@/services/user.service'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  // Supabase session exists = authenticated (for routing)
  // user.value = our app's DB record (for display)
  const supabaseSession = ref<any>(null)
  const loading = ref(false)

  const isAuthenticated = computed(() => !!supabaseSession.value)

  async function init() {
    // Get current session immediately
    const { data } = await supabase.auth.getSession()
    supabaseSession.value = data.session
    if (data.session) {
      fetchAppUser()
    }

    // Keep in sync on auth changes
    supabase.auth.onAuthStateChange((_event, session) => {
      supabaseSession.value = session
      if (session) {
        fetchAppUser()
      } else {
        user.value = null
      }
    })
  }

  // Fetch our app's user record from the backend (non-blocking)
  async function fetchAppUser() {
    try {
      user.value = await userService.getMe()
    } catch {
      // Backend unavailable — keep supabaseSession as auth source of truth
      // User will still be able to navigate, just won't have profile data
    }
  }

  async function loginWithGoogle() {
    loading.value = true
    try {
      await authService.signInWithGoogle()
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    await authService.signOut()
    supabaseSession.value = null
    user.value = null
  }

  return { user, loading, isAuthenticated, supabaseSession, init, loginWithGoogle, logout }
})
