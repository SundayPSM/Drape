<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { tryonService } from '@/services/tryon.service'
import { useTryOnStore } from '@/stores/tryon'
import { useUserStore } from '@/stores/user'
import { useShare } from '@/composables/useShare'
import AppHeader from '@/components/layout/AppHeader.vue'
import CompareSlider from '@/components/results/CompareSlider.vue'
import DrapeButton from '@/components/ui/DrapeButton.vue'
import DrapeSpinner from '@/components/ui/DrapeSpinner.vue'
import type { TryOnJob } from '@/types'

const route = useRoute()
const router = useRouter()
const tryonStore = useTryOnStore()
const userStore = useUserStore()
const { share } = useShare()

const job = ref<TryOnJob | null>(null)
const loading = ref(true)
const saving = ref(false)

const beforeUrl = computed(() => job.value?.human_img_url || userStore.identity?.image_url || '')
const afterUrl = computed(() => job.value?.result_url || '')

onMounted(async () => {
  try {
    // Poll until completed if needed
    let attempts = 0
    while (attempts < 30) {
      const status = await tryonService.getStatus(route.params.jobId as string)
      if (status.status === 'completed') {
        // Load full job from history
        await tryonStore.loadHistory()
        job.value = tryonStore.history.find((j) => j.id === route.params.jobId) || null
        break
      }
      if (status.status === 'failed') break
      await new Promise((r) => setTimeout(r, 2000))
      attempts++
    }
  } finally {
    loading.value = false
  }
})

async function saveLook() {
  if (!job.value) return
  saving.value = true
  try {
    await tryonStore.saveLook(job.value.id)
    job.value = { ...job.value, is_saved: true }
  } finally {
    saving.value = false
  }
}

async function shareResult() {
  const url = `${window.location.origin}/s/${job.value?.share_slug || job.value?.id}`
  await share('Check out my look on Drape', 'I tried this on with Drape AI virtual try-on!', url)
}

function addMoreToLook() {
  if (!job.value?.result_url) return
  tryonStore.buildOnResult(job.value.result_url)
  router.push('/try-on')
}

async function downloadResult() {
  if (!job.value?.result_url) return
  try {
    const res = await fetch(job.value.result_url)
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `drape-look-${job.value.id.slice(0, 8)}.jpg`
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    window.open(job.value.result_url, '_blank')
  }
}
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />
    <div class="page-container py-10 max-w-4xl mx-auto">

      <div v-if="loading" class="flex flex-col items-center gap-4 py-24">
        <DrapeSpinner size="lg" />
        <p class="text-[var(--color-text-muted)] text-sm">Loading your result...</p>
      </div>

      <div v-else-if="job?.result_url" class="animate-fadeUp">
        <!-- Header -->
        <div class="flex items-center justify-between mb-8">
          <div>
            <h1 class="font-display text-3xl font-semibold">Your look</h1>
            <p class="text-[var(--color-text-muted)] text-sm mt-1">
              {{ job.product?.name }} — {{ job.product?.brand }}
            </p>
          </div>
          <button
            class="text-sm text-[var(--color-text-muted)] hover:text-[var(--color-text)] transition-colors"
            @click="router.back()"
          >
            ← Back
          </button>
        </div>

        <div class="grid md:grid-cols-2 gap-8 items-start">
          <!-- Before/After slider -->
          <CompareSlider
            :before-url="beforeUrl"
            :after-url="afterUrl"
            before-label="Original"
            after-label="With item"
          />

          <!-- Actions panel -->
          <div class="space-y-4">
            <!-- Product info -->
            <div class="card p-5">
              <div class="flex gap-4 items-start">
                <div class="w-16 h-16 rounded-xl overflow-hidden bg-drape-bone flex-shrink-0">
                  <img
                    v-if="job.product?.image_url"
                    :src="job.product.image_url"
                    :alt="job.product.name"
                    class="w-full h-full object-cover"
                  />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="text-xs text-[var(--color-text-muted)] mb-0.5">{{ job.product?.brand }}</p>
                  <p class="font-medium text-sm leading-tight">{{ job.product?.name }}</p>
                  <p v-if="job.product?.price" class="text-drape-gold font-semibold mt-1">
                    {{ job.product.currency }} {{ job.product.price.toFixed(2) }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Buy button -->
            <a
              v-if="job.product?.affiliate_url || job.product?.source_url"
              :href="job.product.affiliate_url || job.product.source_url!"
              target="_blank"
              rel="noopener sponsored"
              class="block"
            >
              <DrapeButton variant="gold" size="lg" class="w-full">
                Buy this look →
              </DrapeButton>
            </a>

            <!-- Save / Download / Share -->
            <div class="flex gap-2">
              <DrapeButton
                variant="ghost"
                class="flex-1"
                :loading="saving"
                :disabled="job.is_saved"
                @click="saveLook"
              >
                {{ job.is_saved ? '✓ Saved' : 'Save' }}
              </DrapeButton>
              <DrapeButton variant="ghost" class="flex-1" @click="downloadResult">
                Download
              </DrapeButton>
              <DrapeButton variant="ghost" class="flex-1" @click="shareResult">
                Share
              </DrapeButton>
            </div>

            <!-- Add more to this look -->
            <DrapeButton variant="gold" class="w-full" @click="addMoreToLook">
              + Add more to this look
            </DrapeButton>

            <!-- Try more -->
            <div>
              <RouterLink to="/catalog">
                <DrapeButton variant="ghost" class="w-full">Browse more items</DrapeButton>
              </RouterLink>
            </div>

            <!-- Details -->
            <div class="card p-4 text-xs text-[var(--color-text-muted)] space-y-1">
              <p>Generated with AI · Results may vary</p>
              <p v-if="job.product?.category">Category: {{ job.product.category }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-center py-24">
        <div class="text-4xl mb-4">😔</div>
        <h2 class="font-display text-2xl font-semibold mb-2">Try-on failed</h2>
        <p class="text-[var(--color-text-muted)] mb-6">Something went wrong. Please try again.</p>
        <RouterLink to="/catalog">
          <DrapeButton variant="gold">Try another product</DrapeButton>
        </RouterLink>
      </div>
    </div>
  </div>
</template>
