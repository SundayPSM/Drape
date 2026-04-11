<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUserStore } from '@/stores/user'
import { useTryOnStore } from '@/stores/tryon'
import AppHeader from '@/components/layout/AppHeader.vue'
import DrapeButton from '@/components/ui/DrapeButton.vue'
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue'

const authStore = useAuthStore()
const userStore = useUserStore()
const tryonStore = useTryOnStore()

const hasIdentity = computed(() => userStore.hasIdentity())

onMounted(async () => {
  await Promise.all([userStore.loadIdentity(), tryonStore.loadHistory()])
})
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />
    <div class="page-container py-10">
      <!-- Greeting -->
      <div class="mb-10 animate-fadeUp">
        <h1 class="font-display text-4xl font-semibold mb-1">
          Hello, {{ authStore.user?.name?.split(' ')[0] }} 👋
        </h1>
        <p class="text-[var(--color-text-muted)]">Ready to try something new?</p>
      </div>

      <!-- Setup prompt if no identity -->
      <div v-if="!hasIdentity" class="card p-8 mb-10 flex flex-col md:flex-row items-center gap-6 bg-gradient-to-r from-drape-gold/5 to-transparent border-drape-gold/20">
        <div class="text-5xl">✨</div>
        <div class="flex-1">
          <h2 class="font-display text-xl font-semibold mb-1">Set up your identity first</h2>
          <p class="text-[var(--color-text-muted)] text-sm">Upload your photos to unlock virtual try-on</p>
        </div>
        <RouterLink to="/onboarding">
          <DrapeButton variant="gold">Get started</DrapeButton>
        </RouterLink>
      </div>

      <!-- Quick actions -->
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
        <RouterLink
          v-for="action in quickActions"
          :key="action.to"
          :to="action.to"
          class="card-hover p-6 flex flex-col gap-3 cursor-pointer"
        >
          <span class="text-2xl">{{ action.icon }}</span>
          <div>
            <p class="font-medium text-sm">{{ action.title }}</p>
            <p class="text-xs text-[var(--color-text-muted)]">{{ action.desc }}</p>
          </div>
        </RouterLink>
      </div>

      <!-- Recent try-ons -->
      <div v-if="tryonStore.completedJobs.length > 0">
        <h2 class="font-display text-2xl font-semibold mb-6">Recent try-ons</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <RouterLink
            v-for="job in tryonStore.completedJobs.slice(0, 8)"
            :key="job.id"
            :to="`/result/${job.id}`"
            class="card-hover overflow-hidden group"
          >
            <div class="aspect-[3/4] overflow-hidden">
              <img
                v-if="job.result_url"
                :src="job.result_url"
                :alt="job.product?.name"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              />
              <div v-else class="w-full h-full bg-drape-gold/5 flex items-center justify-center">
                <span class="text-2xl">👗</span>
              </div>
            </div>
            <div class="p-3">
              <p class="text-xs font-medium truncate">{{ job.product?.name }}</p>
              <p class="text-xs text-[var(--color-text-muted)]">{{ job.product?.brand }}</p>
            </div>
          </RouterLink>
        </div>
      </div>
    </div>
  </div>
</template>

<script lang="ts">
const quickActions = [
  { to: '/catalog', icon: '🛍️', title: 'Browse catalog', desc: 'Explore curated items' },
  { to: '/try-on', icon: '🔗', title: 'Paste a URL', desc: 'Try any product online' },
  { to: '/closet', icon: '👗', title: 'My looks', desc: 'All tried garments' },
  { to: '/onboarding', icon: '📸', title: 'Update photos', desc: 'Refresh your identity' },
]
</script>
