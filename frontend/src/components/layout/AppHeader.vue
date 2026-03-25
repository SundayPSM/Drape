<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from '@/components/ui/ThemeToggle.vue'

const router = useRouter()
const authStore = useAuthStore()

const navLinks = computed(() => [
  { name: 'Catalog', to: '/catalog' },
  { name: 'My Closet', to: '/closet' },
])

function logout() {
  authStore.logout()
  router.push('/')
}
</script>

<template>
  <header class="sticky top-0 z-40 bg-[var(--color-bg)]/90 backdrop-blur-md border-b border-[var(--color-border)]">
    <div class="page-container">
      <div class="flex items-center h-16 gap-6">
        <!-- Logo -->
        <RouterLink to="/dashboard" class="font-display text-xl font-semibold tracking-tight mr-4">
          Drape
        </RouterLink>

        <!-- Nav links -->
        <nav class="hidden md:flex items-center gap-1">
          <RouterLink
            v-for="link in navLinks"
            :key="link.to"
            :to="link.to"
            class="px-4 py-2 rounded-full text-sm font-medium text-[var(--color-text-muted)]
                   hover:text-[var(--color-text)] hover:bg-[var(--color-border)]
                   transition-all duration-150 router-link-active:text-drape-gold"
          >
            {{ link.name }}
          </RouterLink>
        </nav>

        <div class="flex-1" />

        <!-- Actions -->
        <div class="flex items-center gap-2">
          <ThemeToggle />
          <template v-if="authStore.isAuthenticated">
            <RouterLink
              to="/catalog"
              class="hidden md:flex btn-gold !py-2 !px-5"
            >
              Try On
            </RouterLink>
            <button
              class="w-9 h-9 rounded-full bg-drape-gold/20 text-drape-gold text-sm font-semibold
                     flex items-center justify-center hover:bg-drape-gold/30 transition-colors"
              @click="router.push('/settings')"
            >
              {{ authStore.user?.name?.charAt(0).toUpperCase() }}
            </button>
          </template>
          <template v-else>
            <RouterLink to="/login" class="btn-ghost !py-2 !px-5 text-sm">Log in</RouterLink>
            <RouterLink to="/register" class="btn-primary !py-2 !px-5 text-sm">Get started</RouterLink>
          </template>
        </div>
      </div>
    </div>
  </header>
</template>
