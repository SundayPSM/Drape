<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { catalogService } from '@/services/catalog.service'
import { useTryOnStore } from '@/stores/tryon'
import { useUserStore } from '@/stores/user'
import { useTryOn } from '@/composables/useTryOn'
import AppHeader from '@/components/layout/AppHeader.vue'
import DrapeButton from '@/components/ui/DrapeButton.vue'
import DrapeSpinner from '@/components/ui/DrapeSpinner.vue'
import type { Product } from '@/types'

const route = useRoute()
const tryonStore = useTryOnStore()
const userStore = useUserStore()
const { status, progress, submitTryOn } = useTryOn()

const product = ref<Product | null>(null)
const loading = ref(true)

onMounted(async () => {
  await userStore.loadIdentity()
  product.value = await catalogService.getProduct(route.params.id as string)
  loading.value = false
})

async function startTryOn() {
  if (!product.value) return
  await submitTryOn(product.value.id)
}
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />
    <div class="page-container py-10">
      <div v-if="loading" class="flex justify-center py-20">
        <DrapeSpinner size="lg" />
      </div>

      <div v-else-if="product" class="grid md:grid-cols-2 gap-12 animate-fadeUp">
        <!-- Product image -->
        <div class="aspect-[3/4] rounded-2xl overflow-hidden bg-drape-bone dark:bg-drape-charcoal">
          <img
            v-if="product.image_url"
            :src="product.image_url"
            :alt="product.name"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center text-6xl opacity-20">
            👗
          </div>
        </div>

        <!-- Product info -->
        <div class="flex flex-col justify-center">
          <p class="text-drape-gold text-sm font-medium tracking-wide uppercase mb-2">
            {{ product.brand }}
          </p>
          <h1 class="font-display text-4xl font-semibold mb-4">{{ product.name }}</h1>
          <p v-if="product.price" class="text-2xl font-semibold mb-4">
            {{ product.currency }} {{ product.price.toFixed(2) }}
          </p>
          <p v-if="product.description" class="text-[var(--color-text-muted)] leading-relaxed mb-8">
            {{ product.description }}
          </p>

          <!-- Try-on section -->
          <div class="space-y-4">
            <!-- Processing state -->
            <div v-if="status === 'processing'" class="card p-6">
              <div class="flex items-center gap-4 mb-4">
                <DrapeSpinner />
                <p class="font-medium">Generating your try-on...</p>
              </div>
              <div class="w-full bg-[var(--color-border)] rounded-full h-2 overflow-hidden">
                <div
                  class="h-full bg-drape-gold rounded-full transition-all duration-500 ease-out"
                  :style="`width: ${progress}%`"
                />
              </div>
              <p class="text-xs text-[var(--color-text-muted)] mt-2 text-right">{{ Math.round(progress) }}%</p>
            </div>

            <template v-else>
              <DrapeButton
                variant="gold"
                size="lg"
                class="w-full"
                @click="startTryOn"
              >
                Try this on me →
              </DrapeButton>
              <a
                v-if="product.affiliate_url || product.source_url"
                :href="product.affiliate_url || product.source_url!"
                target="_blank"
                rel="noopener sponsored"
              >
                <DrapeButton variant="ghost" class="w-full">Buy now</DrapeButton>
              </a>
            </template>
          </div>

          <!-- Identity warning -->
          <div v-if="!userStore.hasIdentity()" class="mt-4 p-4 rounded-xl bg-drape-gold/10 border border-drape-gold/20">
            <p class="text-sm text-drape-gold">
              You need to <RouterLink to="/onboarding" class="underline">set up your identity</RouterLink> first to try on products.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
