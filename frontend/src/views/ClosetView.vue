<script setup lang="ts">
import { onMounted } from 'vue'
import { useTryOnStore } from '@/stores/tryon'
import AppHeader from '@/components/layout/AppHeader.vue'
import DrapeButton from '@/components/ui/DrapeButton.vue'

const tryonStore = useTryOnStore()
onMounted(() => tryonStore.loadHistory())
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />
    <div class="page-container py-10">
      <h1 class="section-title mb-2">My Closet</h1>
      <p class="text-[var(--color-text-muted)] mb-8">Your saved looks</p>

      <div v-if="tryonStore.savedLooks.length === 0" class="text-center py-24">
        <div class="text-4xl mb-4">👗</div>
        <h2 class="font-display text-2xl font-semibold mb-2">No saved looks yet</h2>
        <p class="text-[var(--color-text-muted)] mb-6">Save looks from your try-on results</p>
        <RouterLink to="/catalog">
          <DrapeButton variant="gold">Browse catalog</DrapeButton>
        </RouterLink>
      </div>

      <div v-else class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
        <RouterLink
          v-for="job in tryonStore.savedLooks"
          :key="job.id"
          :to="`/result/${job.id}`"
          class="card-hover overflow-hidden group"
        >
          <div class="aspect-[3/4] overflow-hidden bg-drape-bone dark:bg-drape-charcoal">
            <img
              v-if="job.result_url"
              :src="job.result_url"
              :alt="job.product?.name"
              class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
              loading="lazy"
            />
          </div>
          <div class="p-4">
            <p class="text-xs text-[var(--color-text-muted)]">{{ job.product?.brand }}</p>
            <p class="font-medium text-sm leading-tight mt-0.5 truncate">{{ job.product?.name }}</p>
            <p v-if="job.product?.price" class="text-drape-gold text-sm font-semibold mt-1">
              {{ job.product.currency }} {{ job.product.price.toFixed(0) }}
            </p>
          </div>
        </RouterLink>
      </div>
    </div>
  </div>
</template>
