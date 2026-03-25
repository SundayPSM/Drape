<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import DrapeButton from '@/components/ui/DrapeButton.vue'
import ThemeToggle from '@/components/ui/ThemeToggle.vue'

const authStore = useAuthStore()
const uiStore = useUIStore()
const router = useRouter()

function logout() {
  authStore.logout()
  router.push('/')
}
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />
    <div class="page-container py-10 max-w-xl">
      <h1 class="section-title mb-8">Settings</h1>

      <!-- Profile -->
      <div class="card p-6 mb-4">
        <h2 class="font-semibold mb-4">Profile</h2>
        <div class="flex items-center gap-4">
          <div class="w-14 h-14 rounded-full bg-drape-gold/20 text-drape-gold text-xl font-bold flex items-center justify-center">
            {{ authStore.user?.name?.charAt(0).toUpperCase() }}
          </div>
          <div>
            <p class="font-medium">{{ authStore.user?.name }}</p>
            <p class="text-sm text-[var(--color-text-muted)]">{{ authStore.user?.email }}</p>
          </div>
        </div>
      </div>

      <!-- Appearance -->
      <div class="card p-6 mb-4">
        <h2 class="font-semibold mb-4">Appearance</h2>
        <div class="flex items-center justify-between">
          <div>
            <p class="font-medium text-sm">Dark mode</p>
            <p class="text-xs text-[var(--color-text-muted)]">Switch between light and dark</p>
          </div>
          <ThemeToggle />
        </div>
      </div>

      <!-- Identity -->
      <div class="card p-6 mb-4">
        <h2 class="font-semibold mb-4">Your identity</h2>
        <p class="text-sm text-[var(--color-text-muted)] mb-4">
          Update your photos to improve try-on realism
        </p>
        <RouterLink to="/onboarding">
          <DrapeButton variant="ghost">Update photos</DrapeButton>
        </RouterLink>
      </div>

      <!-- Sign out -->
      <div class="card p-6">
        <h2 class="font-semibold mb-4">Account</h2>
        <DrapeButton variant="ghost" @click="logout">Sign out</DrapeButton>
      </div>
    </div>
  </div>
</template>
