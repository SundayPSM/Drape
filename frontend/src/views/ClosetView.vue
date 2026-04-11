<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useTryOnStore } from '@/stores/tryon'
import AppHeader from '@/components/layout/AppHeader.vue'
import DrapeButton from '@/components/ui/DrapeButton.vue'
import type { TryOnJob } from '@/types'

const tryonStore = useTryOnStore()
const activeTab = ref<'all' | 'saved'>('all')

onMounted(() => tryonStore.loadHistory())

const displayedJobs = computed<TryOnJob[]>(() =>
  activeTab.value === 'saved' ? tryonStore.savedLooks : tryonStore.completedJobs
)

async function downloadImage(job: TryOnJob, e: Event) {
  e.preventDefault()
  e.stopPropagation()
  if (!job.result_url) return
  try {
    const res = await fetch(job.result_url)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `drape-look-${job.id.slice(0, 8)}.jpg`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    window.open(job.result_url, '_blank')
  }
}
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />
    <div class="page-container py-10">

      <!-- Header -->
      <div class="flex items-end justify-between mb-8">
        <div>
          <h1 class="font-display text-4xl font-semibold mb-1">My Looks</h1>
          <p class="text-[var(--color-text-muted)]">Every garment you've tried on</p>
        </div>
        <RouterLink to="/try-on">
          <DrapeButton variant="gold">+ New try-on</DrapeButton>
        </RouterLink>
      </div>

      <!-- Tabs -->
      <div class="flex gap-1 mb-8 border-b border-[var(--color-border)]">
        <button
          v-for="tab in [{ key: 'all', label: 'All looks' }, { key: 'saved', label: 'Saved' }]"
          :key="tab.key"
          class="px-5 py-2.5 text-sm font-medium transition-colors relative"
          :class="activeTab === tab.key
            ? 'text-drape-gold'
            : 'text-[var(--color-text-muted)] hover:text-[var(--color-text)]'"
          @click="activeTab = tab.key as 'all' | 'saved'"
        >
          {{ tab.label }}
          <span
            v-if="activeTab === tab.key"
            class="absolute bottom-0 left-0 right-0 h-0.5 bg-drape-gold rounded-t-full"
          />
        </button>
      </div>

      <!-- Empty state -->
      <div v-if="displayedJobs.length === 0" class="text-center py-24">
        <div class="text-5xl mb-4">{{ activeTab === 'saved' ? '🤍' : '✨' }}</div>
        <h2 class="font-display text-2xl font-semibold mb-2">
          {{ activeTab === 'saved' ? 'No saved looks yet' : 'No try-ons yet' }}
        </h2>
        <p class="text-[var(--color-text-muted)] mb-6">
          {{ activeTab === 'saved' ? 'Save looks from your results to find them here' : 'Paste a product URL and try it on your model' }}
        </p>
        <RouterLink :to="activeTab === 'saved' ? '/closet' : '/try-on'">
          <DrapeButton variant="gold">
            {{ activeTab === 'saved' ? 'View all looks' : 'Try something on' }}
          </DrapeButton>
        </RouterLink>
      </div>

      <!-- Grid -->
      <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
        <div
          v-for="job in displayedJobs"
          :key="job.id"
          class="group relative"
        >
          <RouterLink :to="`/result/${job.id}`" class="block card-hover overflow-hidden">
            <!-- Result image -->
            <div class="aspect-[3/4] overflow-hidden bg-[var(--color-surface-raised)]">
              <img
                v-if="job.result_url"
                :src="job.result_url"
                :alt="job.product?.name"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                loading="lazy"
              />
              <div v-else class="w-full h-full flex items-center justify-center">
                <span class="text-3xl">👗</span>
              </div>
            </div>

            <!-- Info -->
            <div class="p-3">
              <p class="text-xs text-[var(--color-text-muted)] truncate">{{ job.product?.brand || 'Custom' }}</p>
              <p class="font-medium text-sm leading-tight mt-0.5 truncate">{{ job.product?.name || 'Try-on' }}</p>
            </div>
          </RouterLink>

          <!-- Download button — overlaid top-right -->
          <button
            v-if="job.result_url"
            class="absolute top-2 right-2 w-8 h-8 rounded-full bg-black/60 text-white flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/80"
            title="Download"
            @click="downloadImage(job, $event)"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
              <polyline points="7 10 12 15 17 10"/>
              <line x1="12" y1="15" x2="12" y2="3"/>
            </svg>
          </button>

          <!-- Saved badge -->
          <div
            v-if="job.is_saved"
            class="absolute top-2 left-2 w-6 h-6 rounded-full bg-drape-gold flex items-center justify-center"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3 text-black" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
