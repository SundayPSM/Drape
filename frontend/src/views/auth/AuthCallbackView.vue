<script setup lang="ts">
/**
 * Supabase redirects here after Google OAuth.
 * We wait for the auth state change event before navigating,
 * to ensure the session is fully established.
 */
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/services/supabase'
import DrapeSpinner from '@/components/ui/DrapeSpinner.vue'

const router = useRouter()

let subscription: any = null

onMounted(() => {
  // Listen for the SIGNED_IN event which fires once tokens are processed
  const { data } = supabase.auth.onAuthStateChange((event, session) => {
    if (event === 'SIGNED_IN' && session) {
      router.replace('/dashboard')
    } else if (event === 'SIGNED_OUT' || (!session && event !== 'INITIAL_SESSION')) {
      router.replace('/login')
    }
  })
  subscription = data.subscription

  // Fallback: if session already exists (page refresh on callback route)
  supabase.auth.getSession().then(({ data: { session } }) => {
    if (session) {
      router.replace('/dashboard')
    }
  })
})

onUnmounted(() => {
  subscription?.unsubscribe()
})
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center gap-4">
    <DrapeSpinner size="lg" />
    <p class="text-[var(--color-text-muted)] text-sm">Signing you in...</p>
  </div>
</template>
