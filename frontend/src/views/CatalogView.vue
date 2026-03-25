<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { catalogService } from '@/services/catalog.service'
import { useTryOnStore } from '@/stores/tryon'
import { useUIStore } from '@/stores/ui'
import AppHeader from '@/components/layout/AppHeader.vue'
import DrapeInput from '@/components/ui/DrapeInput.vue'
import DrapeButton from '@/components/ui/DrapeButton.vue'
import SkeletonLoader from '@/components/ui/SkeletonLoader.vue'
import type { Product, ProductCategory } from '@/types'

const router = useRouter()
const tryonStore = useTryOnStore()
const uiStore = useUIStore()

const products = ref<Product[]>([])
const loading = ref(true)
const scrapeUrl = ref('')
const scraping = ref(false)
const selectedCategory = ref<ProductCategory | ''>('')
const searchQuery = ref('')

const categories: { label: string; value: ProductCategory | '' }[] = [
  { label: 'All', value: '' },
  { label: 'Tops', value: 'tops' },
  { label: 'Dresses', value: 'dresses' },
  { label: 'Outerwear', value: 'outerwear' },
  { label: 'Bottoms', value: 'bottoms' },
  { label: 'Footwear', value: 'footwear' },
  { label: 'Accessories', value: 'accessories' },
]

async function loadProducts() {
  loading.value = true
  try {
    const res = await catalogService.listProducts({
      category: selectedCategory.value || undefined,
      q: searchQuery.value || undefined,
    })
    products.value = res.items
  } finally {
    loading.value = false
  }
}

async function scrapeProductUrl() {
  if (!scrapeUrl.value) return
  scraping.value = true
  try {
    const product = await catalogService.scrapeProduct(scrapeUrl.value)
    products.value.unshift(product)
    scrapeUrl.value = ''
    uiStore.toast('Product added!', 'success')
  } catch (err: any) {
    uiStore.toast(err?.response?.data?.detail || 'Could not load product from URL', 'error')
  } finally {
    scraping.value = false
  }
}

function selectProduct(product: Product) {
  tryonStore.selectProduct(product)
  router.push(`/product/${product.id}`)
}

onMounted(loadProducts)
watch([selectedCategory, searchQuery], loadProducts)
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />
    <div class="page-container py-10">
      <h1 class="section-title mb-2">Catalog</h1>
      <p class="text-[var(--color-text-muted)] mb-8">Browse items or paste any URL to try on</p>

      <!-- URL scraper -->
      <div class="card p-4 mb-8 flex flex-col sm:flex-row gap-3">
        <DrapeInput
          v-model="scrapeUrl"
          placeholder="Paste any product URL — Zara, ASOS, H&M..."
          class="flex-1"
          @keydown.enter="scrapeProductUrl"
        />
        <DrapeButton variant="gold" :loading="scraping" @click="scrapeProductUrl">
          Try it on
        </DrapeButton>
      </div>

      <!-- Filters -->
      <div class="flex gap-2 flex-wrap mb-8">
        <button
          v-for="cat in categories"
          :key="cat.value"
          class="px-4 py-2 rounded-full text-sm font-medium border transition-all duration-150"
          :class="selectedCategory === cat.value
            ? 'bg-drape-gold text-drape-obsidian border-drape-gold'
            : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-drape-gold/50'"
          @click="selectedCategory = cat.value"
        >
          {{ cat.label }}
        </button>
      </div>

      <!-- Product grid -->
      <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-5">
        <template v-if="loading">
          <SkeletonLoader v-for="i in 8" :key="i" class="aspect-[3/4]" />
        </template>
        <template v-else>
          <div
            v-for="product in products"
            :key="product.id"
            class="card-hover cursor-pointer group overflow-hidden"
            @click="selectProduct(product)"
          >
            <div class="aspect-[3/4] overflow-hidden bg-drape-bone dark:bg-drape-charcoal">
              <img
                v-if="product.image_url"
                :src="product.image_url"
                :alt="product.name"
                class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                loading="lazy"
              />
              <div v-else class="w-full h-full flex items-center justify-center text-4xl opacity-30">
                👗
              </div>
            </div>
            <div class="p-4">
              <p class="text-xs text-[var(--color-text-muted)] mb-1">{{ product.brand }}</p>
              <p class="font-medium text-sm leading-tight mb-2 line-clamp-2">{{ product.name }}</p>
              <div class="flex items-center justify-between">
                <p v-if="product.price" class="text-sm font-semibold">
                  {{ product.currency }} {{ product.price.toFixed(0) }}
                </p>
                <span class="text-xs bg-drape-gold/10 text-drape-gold px-2 py-0.5 rounded-full">
                  Try on →
                </span>
              </div>
            </div>
          </div>
        </template>

        <div v-if="!loading && products.length === 0" class="col-span-full text-center py-16">
          <div class="text-4xl mb-4">🔍</div>
          <p class="font-medium mb-2">No products found</p>
          <p class="text-sm text-[var(--color-text-muted)]">Try a different category or paste a product URL above</p>
        </div>
      </div>
    </div>
  </div>
</template>
