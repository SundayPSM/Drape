import { supabase } from './supabase'
import type { Session, User as SupabaseUser } from '@supabase/supabase-js'

export const authService = {
  /**
   * Trigger Google OAuth — redirects to Google, then back to /auth/callback
   */
  async signInWithGoogle(): Promise<void> {
    const { error } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
        queryParams: {
          access_type: 'offline',
          prompt: 'consent',
        },
      },
    })
    if (error) throw error
  },

  async signOut(): Promise<void> {
    await supabase.auth.signOut()
  },

  async getSession(): Promise<Session | null> {
    const { data } = await supabase.auth.getSession()
    return data.session
  },

  async getAccessToken(): Promise<string | null> {
    const session = await authService.getSession()
    return session?.access_token ?? null
  },

  isAuthenticated(): boolean {
    // Synchronous check — Supabase persists session in localStorage
    const raw = localStorage.getItem('sb-' + import.meta.env.VITE_SUPABASE_URL?.split('//')[1]?.split('.')[0] + '-auth-token')
    if (!raw) return false
    try {
      const parsed = JSON.parse(raw)
      return !!parsed?.access_token
    } catch {
      return false
    }
  },

  onAuthStateChange(callback: (user: SupabaseUser | null) => void) {
    return supabase.auth.onAuthStateChange((_event, session) => {
      callback(session?.user ?? null)
    })
  },
}
