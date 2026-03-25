<script setup lang="ts">
import { onMounted } from 'vue'
import { useTryOnStore } from '@/stores/tryon'
import { useRouter } from 'vue-router'
import AppHeader from '@/components/layout/AppHeader.vue'
import DrapeSpinner from '@/components/ui/DrapeSpinner.vue'
import DrapeButton from '@/components/ui/DrapeButton.vue'

const router = useRouter()
const tryonStore = useTryOnStore()

onMounted(() => {
  if (!tryonStore.activeJobId) {
    router.push('/catalog')
  }
})
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />
    <div class="page-container py-10 max-w-xl mx-auto text-center">
      <div class="card p-12 flex flex-col items-center gap-6">
        <!-- Animated diffusion visualization -->
        <div class="relative w-24 h-24">
          <div class="absolute inset-0 rounded-full bg-drape-gold/20 animate-ping" />
          <div class="relative w-24 h-24 rounded-full bg-drape-gold/10 flex items-center justify-center">
            <DrapeSpinner size="lg" />
          </div>
        </div>

        <div>
          <h2 class="font-display text-2xl font-semibold mb-2">Creating your look</h2>
          <p class="text-[var(--color-text-muted)] text-sm">
            Our AI is draping the selected item onto your identity.
            This usually takes 15–30 seconds.
          </p>
        </div>

        <div class="w-full max-w-xs">
          <div class="flex justify-between text-xs text-[var(--color-text-muted)] mb-2">
            <span>Processing</span>
            <span>{{ tryonStore.activeStatus }}</span>
          </div>
          <div class="w-full bg-[var(--color-border)] rounded-full h-1.5 overflow-hidden">
            <div class="h-full bg-drape-gold rounded-full animate-pulse w-3/4 transition-all" />
          </div>
        </div>

        <DrapeButton variant="ghost" size="sm" @click="router.push('/catalog')">
          Cancel
        </DrapeButton>
      </div>
    </div>
  </div>
</template>
