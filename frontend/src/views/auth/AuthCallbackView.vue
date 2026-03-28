<script setup lang="ts">
/**
 * Supabase redirects here after Google OAuth.
 * The Supabase JS client automatically parses the URL hash/query params
 * and sets the session. We just wait for the auth state change and navigate.
 */
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { supabase } from '@/services/supabase'
import DrapeSpinner from '@/components/ui/DrapeSpinner.vue'

const router = useRouter()

onMounted(async () => {
  // Supabase client picks up the token from the URL automatically
  const { data } = await supabase.auth.getSession()
  if (data.session) {
    router.replace('/dashboard')
  } else {
    router.replace('/login')
  }
})
</script>

<template>
  <div class="min-h-screen flex flex-col items-center justify-center gap-4">
    <DrapeSpinner size="lg" />
    <p class="text-[var(--color-text-muted)] text-sm">Signing you in...</p>
  </div>
</template>
