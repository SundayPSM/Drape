<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import DrapeInput from '@/components/ui/DrapeInput.vue'
import DrapeButton from '@/components/ui/DrapeButton.vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const uiStore = useUIStore()

const email = ref('')
const password = ref('')
const error = ref('')

async function submit() {
  error.value = ''
  try {
    await authStore.login(email.value, password.value)
    const redirect = route.query.redirect as string || '/dashboard'
    router.push(redirect)
  } catch (err: any) {
    error.value = err?.response?.data?.detail || 'Login failed. Please try again.'
  }
}
</script>

<template>
  <div class="min-h-screen flex items-center justify-center px-4">
    <div class="w-full max-w-md animate-scaleIn">
      <div class="text-center mb-10">
        <RouterLink to="/" class="font-display text-2xl font-semibold">Drape</RouterLink>
        <h1 class="font-display text-3xl font-semibold mt-6 mb-2">Welcome back</h1>
        <p class="text-[var(--color-text-muted)] text-sm">Sign in to your account</p>
      </div>

      <div class="card p-8">
        <form @submit.prevent="submit" class="flex flex-col gap-5">
          <DrapeInput v-model="email" label="Email" type="email" placeholder="you@example.com" />
          <DrapeInput v-model="password" label="Password" type="password" placeholder="••••••••" />
          <p v-if="error" class="text-sm text-red-500 text-center">{{ error }}</p>
          <DrapeButton type="submit" variant="gold" :loading="authStore.loading" class="w-full mt-2">
            Sign in
          </DrapeButton>
        </form>
      </div>

      <p class="text-center text-sm text-[var(--color-text-muted)] mt-6">
        Don't have an account?
        <RouterLink to="/register" class="text-drape-gold hover:underline ml-1">Sign up</RouterLink>
      </p>
    </div>
  </div>
</template>
