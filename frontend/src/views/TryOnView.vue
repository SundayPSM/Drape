<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useTryOnStore } from '@/stores/tryon'
import { productService } from '@/services/product.service'
import { tryonService } from '@/services/tryon.service'
import AppHeader from '@/components/layout/AppHeader.vue'
import DrapeButton from '@/components/ui/DrapeButton.vue'
import DrapeSpinner from '@/components/ui/DrapeSpinner.vue'
import type { ProductCategory, TryOnFit } from '@/types'

const router = useRouter()
const userStore = useUserStore()
const tryonStore = useTryOnStore()

// ── State ──────────────────────────────────────────────────────────────────
type Phase = 'idle' | 'submitting' | 'processing'
const phase = ref<Phase>('idle')
const error = ref<string | null>(null)
const jobId = ref<string | null>(null)
let pollTimer: ReturnType<typeof setTimeout> | null = null

const identity = computed(() => userStore.identity)

// ── Iterative base ─────────────────────────────────────────────────────────
// If the user clicked "Add more to this look", the previous result image is
// used as the person base instead of the raw identity portrait.
const baseResultUrl = computed(() => tryonStore.baseResultUrl)
const personImageUrl = computed(() => baseResultUrl.value || identity.value?.image_url || null)
const isLayering = computed(() => !!baseResultUrl.value)

// ── Pose reference ─────────────────────────────────────────────────────────
const poseUrlInput = ref('')
const poseImageUrl = ref<string | null>(null)
const poseExtracting = ref(false)
const poseError = ref<string | null>(null)

async function extractPoseImage() {
  const url = poseUrlInput.value.trim()
  if (!url) return
  poseError.value = null
  poseExtracting.value = true
  try {
    const result = await productService.extractImage(url)
    poseImageUrl.value = result.image_url
    poseUrlInput.value = ''
  } catch (e: any) {
    poseError.value = e?.response?.data?.detail || 'Could not load image from this URL.'
  } finally {
    poseExtracting.value = false
  }
}

function clearPose() {
  poseImageUrl.value = null
  poseUrlInput.value = ''
  poseError.value = null
}

// ── Garment slots ──────────────────────────────────────────────────────────
interface GarmentSlot {
  id: string
  label: string
  icon: string
  category: ProductCategory
  imageUrl: string | null
  sourceUrl: string | null
  title: string | null
  fit: TryOnFit
  urlInput: string
  extracting: boolean
  error: string | null
}

const SLOT_DEFS: { id: string; label: string; icon: string; category: ProductCategory }[] = [
  { id: 'top',        label: 'Top / Shirt',  icon: '👕', category: 'tops' },
  { id: 'bottom',     label: 'Pants / Skirt', icon: '👖', category: 'bottoms' },
  { id: 'outerwear',  label: 'Jacket',        icon: '🧥', category: 'outerwear' },
  { id: 'footwear',   label: 'Shoes',         icon: '👟', category: 'footwear' },
  { id: 'watch',      label: 'Watch',         icon: '⌚', category: 'watches' },
  { id: 'sunglasses', label: 'Sunglasses',    icon: '🕶️', category: 'sunglasses' },
]

const slots = ref<GarmentSlot[]>(
  SLOT_DEFS.map((d) => ({
    ...d,
    imageUrl: null, sourceUrl: null, title: null,
    fit: 'regular', urlInput: '', extracting: false, error: null,
  }))
)

const filledSlots = computed(() => slots.value.filter((s) => s.imageUrl))
const hasAnyGarment = computed(() => filledSlots.value.length > 0)

const FITS: { value: TryOnFit; label: string }[] = [
  { value: 'slim',      label: 'Slim' },
  { value: 'regular',   label: 'Regular' },
  { value: 'oversized', label: 'Oversized' },
]

onMounted(async () => {
  await userStore.loadIdentity()
  if (!userStore.hasIdentity()) router.push('/onboarding')
})

async function extractForSlot(slot: GarmentSlot) {
  const url = slot.urlInput.trim()
  if (!url) return
  slot.error = null
  slot.extracting = true
  try {
    const result = await productService.extractImage(url)
    slot.imageUrl = result.image_url
    slot.sourceUrl = result.source_url
    slot.title = result.title
    slot.urlInput = ''
  } catch (e: any) {
    slot.error = e?.response?.data?.detail || 'Could not extract image from this URL.'
  } finally {
    slot.extracting = false
  }
}

function clearSlot(slot: GarmentSlot) {
  slot.imageUrl = null; slot.sourceUrl = null; slot.title = null
  slot.urlInput = ''; slot.error = null; slot.fit = 'regular'
}

// ── Submit ─────────────────────────────────────────────────────────────────
async function startTryOn() {
  if (!hasAnyGarment.value || !identity.value?.id) return
  error.value = null
  phase.value = 'submitting'

  try {
    const filled = filledSlots.value
    const products = await Promise.all(
      filled.map((slot) =>
        productService.quickAdd({
          image_url: slot.imageUrl!,
          source_url: slot.sourceUrl || slot.imageUrl!,
          category: slot.category,
          name: slot.title || undefined,
        })
      )
    )

    const primary = products[0]
    const primarySlot = filled[0]
    const extraGarments = filled.slice(1).map((slot) => ({
      image_url: slot.imageUrl!,
      source_url: slot.sourceUrl || slot.imageUrl!,
      category: slot.category,
      name: slot.title || undefined,
      fit: slot.fit,
    }))

    const job = await tryonService.submitOutfit(
      primary.id,
      identity.value!.id,
      primarySlot.fit,
      extraGarments,
      poseImageUrl.value,
      baseResultUrl.value,
    )

    jobId.value = job.job_id
    tryonStore.setActiveJob(job.job_id)
    tryonStore.clearBaseResult()  // consumed — clear so next fresh try-on starts clean
    phase.value = 'processing'
    pollStatus()
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Failed to start try-on. Please try again.'
    phase.value = 'idle'
  }
}

function pollStatus() {
  if (!jobId.value) return
  pollTimer = setTimeout(async () => {
    try {
      const status = await tryonService.getStatus(jobId.value!)
      tryonStore.updateJobStatus(status.status, status.result_url)
      if (status.status === 'completed') {
        router.push(`/result/${jobId.value}`)
      } else if (status.status === 'failed') {
        error.value = status.error_message || 'Try-on failed. Please try again.'
        phase.value = 'idle'
      } else {
        pollStatus()
      }
    } catch {
      pollStatus()
    }
  }, 3000)
}

function cancelProcessing() {
  if (pollTimer) clearTimeout(pollTimer)
  phase.value = 'idle'
}

function discardBase() {
  tryonStore.clearBaseResult()
}
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />

    <div class="page-container py-10">
      <div class="mb-8">
        <h1 class="font-display text-3xl font-semibold mb-1">
          {{ isLayering ? 'Add More to Your Look' : 'Build Your Outfit' }}
        </h1>
        <p class="text-[var(--color-text-muted)] text-sm">
          {{ isLayering
            ? 'Your previous result is the base — pick new garments to layer on top'
            : 'Add garments, pick a pose reference — AI does the rest'
          }}
        </p>
      </div>

      <!-- Processing -->
      <div v-if="phase === 'processing'" class="max-w-md mx-auto">
        <div class="card p-12 flex flex-col items-center gap-6 text-center">
          <div class="relative w-24 h-24">
            <div class="absolute inset-0 rounded-full bg-drape-gold/20 animate-ping" />
            <div class="relative w-24 h-24 rounded-full bg-drape-gold/10 flex items-center justify-center">
              <DrapeSpinner size="lg" />
            </div>
          </div>
          <div>
            <h2 class="font-display text-2xl font-semibold mb-2">Creating your look</h2>
            <p class="text-[var(--color-text-muted)] text-sm">
              AI is styling {{ filledSlots.length > 1 ? 'your full outfit' : 'the garment' }} onto your model.<br />
              Usually takes 20–40 seconds.
            </p>
          </div>
          <div class="w-full">
            <div class="w-full bg-[var(--color-border)] rounded-full h-1.5 overflow-hidden">
              <div class="h-full bg-drape-gold rounded-full animate-pulse w-3/4" />
            </div>
          </div>
          <DrapeButton variant="ghost" size="sm" @click="cancelProcessing">Cancel</DrapeButton>
        </div>
      </div>

      <!-- Builder -->
      <div v-else class="flex flex-col gap-6 max-w-6xl mx-auto">

        <!-- Row 1: Model + Garments -->
        <div class="grid grid-cols-1 lg:grid-cols-[240px_1fr] gap-6">

          <!-- Your Model -->
          <div class="card p-5 flex flex-col gap-4">
            <!-- Layering banner -->
            <div v-if="isLayering" class="flex items-center justify-between">
              <div>
                <p class="text-xs font-semibold text-drape-gold uppercase tracking-widest">Adding to look</p>
                <p class="text-[10px] text-[var(--color-text-muted)] mt-0.5">Building on your previous result</p>
              </div>
              <button
                class="text-[10px] text-[var(--color-text-muted)] hover:text-[var(--color-text)] underline"
                @click="discardBase"
              >Start fresh</button>
            </div>
            <p v-else class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Your Model</p>

            <div v-if="personImageUrl" class="relative rounded-xl overflow-hidden aspect-[3/4] bg-[var(--color-surface-raised)]">
              <img :src="personImageUrl" alt="Base image" class="w-full h-full object-cover" />
              <!-- Layering indicator -->
              <div v-if="isLayering" class="absolute bottom-2 left-2 right-2 bg-black/60 rounded-lg px-2 py-1 text-[10px] text-drape-gold text-center">
                Previous result — adding new items on top
              </div>
            </div>
            <div v-else class="rounded-xl aspect-[3/4] bg-[var(--color-surface-raised)] flex items-center justify-center">
              <div class="text-center text-[var(--color-text-muted)]">
                <div class="text-4xl mb-2">👤</div>
                <p class="text-sm mb-2">No model yet</p>
                <RouterLink to="/onboarding" class="text-drape-gold text-xs underline">Set up identity</RouterLink>
              </div>
            </div>
          </div>

          <!-- Garment slots -->
          <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div v-for="slot in slots" :key="slot.id" class="card p-4 flex flex-col gap-3">

              <!-- Header -->
              <div class="flex items-center gap-2">
                <span class="text-lg">{{ slot.icon }}</span>
                <span class="text-xs font-semibold">{{ slot.label }}</span>
                <span v-if="slot.imageUrl" class="ml-auto w-2 h-2 rounded-full bg-drape-gold flex-shrink-0" />
              </div>

              <!-- Empty -->
              <template v-if="!slot.imageUrl">
                <div class="flex gap-2">
                  <input
                    v-model="slot.urlInput"
                    type="url"
                    placeholder="Paste URL..."
                    class="flex-1 px-3 py-2 rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-xs focus:outline-none focus:border-drape-gold transition-colors min-w-0"
                    :disabled="slot.extracting"
                    @keydown.enter="extractForSlot(slot)"
                  />
                  <button
                    class="w-8 h-8 rounded-lg bg-drape-gold text-black font-bold flex items-center justify-center hover:bg-drape-gold/80 transition-colors disabled:opacity-40 flex-shrink-0"
                    :disabled="!slot.urlInput.trim() || slot.extracting"
                    @click="extractForSlot(slot)"
                  >
                    <DrapeSpinner v-if="slot.extracting" size="sm" />
                    <span v-else class="text-base leading-none">+</span>
                  </button>
                </div>
                <p v-if="slot.error" class="text-red-400 text-[10px]">{{ slot.error }}</p>
              </template>

              <!-- Filled -->
              <template v-else>
                <div class="relative">
                  <div class="rounded-xl overflow-hidden aspect-square bg-[var(--color-surface-raised)]">
                    <img :src="slot.imageUrl" :alt="slot.label" class="w-full h-full object-contain" />
                  </div>
                  <button
                    class="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-black/60 text-white text-xs flex items-center justify-center hover:bg-black/80"
                    @click="clearSlot(slot)"
                  >✕</button>
                </div>
                <p v-if="slot.title" class="text-[10px] font-medium truncate text-[var(--color-text-muted)]">{{ slot.title }}</p>
                <!-- Fit -->
                <div class="flex gap-1">
                  <button
                    v-for="fit in FITS"
                    :key="fit.value"
                    class="flex-1 py-1 rounded-md border text-[9px] font-medium transition-all"
                    :class="slot.fit === fit.value
                      ? 'border-drape-gold bg-drape-gold/10 text-drape-gold'
                      : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-drape-gold/40'"
                    @click="slot.fit = fit.value"
                  >{{ fit.label }}</button>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- Row 2: Pose Reference + Outfit Summary + Generate -->
        <div class="grid grid-cols-1 md:grid-cols-[1fr_auto] gap-6 items-start">

          <!-- Pose Reference -->
          <div class="card p-5">
            <div class="flex items-start gap-3 mb-4">
              <div>
                <p class="text-xs font-semibold text-[var(--color-text-muted)] uppercase tracking-widest">Pose Reference</p>
                <p class="text-xs text-[var(--color-text-muted)] mt-0.5">
                  Paste any photo — AI copies the body pose and facial expression from it
                </p>
              </div>
            </div>

            <div v-if="!poseImageUrl" class="flex gap-2">
              <input
                v-model="poseUrlInput"
                type="url"
                placeholder="Paste any image URL or product page URL..."
                class="flex-1 px-4 py-2.5 rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-sm focus:outline-none focus:border-drape-gold transition-colors"
                :disabled="poseExtracting"
                @keydown.enter="extractPoseImage"
              />
              <button
                class="w-11 h-11 rounded-lg bg-[var(--color-surface-raised)] border border-[var(--color-border)] text-sm flex items-center justify-center hover:border-drape-gold/50 transition-colors disabled:opacity-40 flex-shrink-0"
                :disabled="!poseUrlInput.trim() || poseExtracting"
                @click="extractPoseImage"
              >
                <DrapeSpinner v-if="poseExtracting" size="sm" />
                <span v-else class="text-[var(--color-text-muted)]">↗</span>
              </button>
            </div>
            <p v-if="poseError" class="mt-2 text-red-400 text-xs">{{ poseError }}</p>

            <!-- Pose preview -->
            <div v-if="poseImageUrl" class="flex gap-4 items-start">
              <div class="relative flex-shrink-0">
                <div class="w-28 rounded-xl overflow-hidden aspect-[3/4] bg-[var(--color-surface-raised)]">
                  <img :src="poseImageUrl" alt="Pose reference" class="w-full h-full object-cover" />
                </div>
                <button
                  class="absolute top-1.5 right-1.5 w-6 h-6 rounded-full bg-black/60 text-white text-xs flex items-center justify-center hover:bg-black/80"
                  @click="clearPose"
                >✕</button>
              </div>
              <div class="text-xs text-[var(--color-text-muted)] space-y-1 pt-1">
                <p class="font-semibold text-[var(--color-text)]">Pose & expression detected</p>
                <p>AI will read the body position, head angle, and facial expression from this photo and apply them to your model.</p>
                <p class="text-drape-gold">Only pose is copied — your face and identity are preserved.</p>
              </div>
            </div>

            <!-- No pose hint -->
            <p v-if="!poseImageUrl" class="mt-3 text-[10px] text-[var(--color-text-muted)]">
              Optional — without a reference, model stands in a neutral front-facing pose.
            </p>
          </div>

          <!-- Summary + Generate -->
          <div class="flex flex-col gap-3 min-w-[200px]">
            <div class="card p-4 text-xs space-y-2">
              <p class="font-semibold">Summary</p>
              <div class="space-y-1 text-[var(--color-text-muted)]">
                <p>
                  <span class="font-medium text-[var(--color-text)]">{{ filledSlots.length }}</span>
                  garment{{ filledSlots.length !== 1 ? 's' : '' }}
                  <span v-if="filledSlots.length === 0" class="text-[var(--color-text-muted)]"> — add at least one</span>
                </p>
                <p v-for="slot in filledSlots" :key="slot.id" class="flex items-center gap-1.5">
                  <span>{{ slot.icon }}</span>
                  <span class="truncate">{{ slot.title || slot.label }}</span>
                  <span class="text-[9px] text-drape-gold/70 flex-shrink-0">{{ slot.fit }}</span>
                </p>
                <div class="pt-1 border-t border-[var(--color-border)]">
                  <p v-if="poseImageUrl" class="flex items-center gap-1">
                    <span>📸</span> Pose reference set
                  </p>
                  <p v-else class="text-[var(--color-text-muted)]">No pose ref — neutral stance</p>
                </div>
              </div>
            </div>

            <DrapeButton
              variant="gold"
              class="w-full"
              :disabled="!hasAnyGarment || phase === 'submitting'"
              @click="startTryOn"
            >
              <DrapeSpinner v-if="phase === 'submitting'" size="sm" class="mr-2" />
              {{ phase === 'submitting' ? 'Generating...' : 'Generate Look →' }}
            </DrapeButton>

            <p v-if="error" class="text-red-400 text-xs text-center">{{ error }}</p>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>
