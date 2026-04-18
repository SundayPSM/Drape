<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useUIStore } from '@/stores/ui'
import { userService } from '@/services/user.service'
import DrapeButton from '@/components/ui/DrapeButton.vue'
import DrapeSpinner from '@/components/ui/DrapeSpinner.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import { useGuidedUpload } from '@/composables/useFileUpload'
import type { GuidedPhotoType } from '@/composables/useFileUpload'

const router = useRouter()
const userStore = useUserStore()
const uiStore = useUIStore()
const { slots, setSlotFile, clearSlot, filledCount, allSlotsFilled } = useGuidedUpload()

type Step = 'profile' | 'upload' | 'generating' | 'angles' | 'pick' | 'done'
const step = ref<Step>('profile')
const generatingMessage = ref('Uploading your photos...')

// ── Profile ───────────────────────────────────────────────────────────────────
const profile = reactive({
  gender: '',
  age: null as number | null,
  height_cm: null as number | null,
  weight_kg: null as number | null,
  usual_size: '',
  skin_tone: '',
})

const GENDERS = ['Male', 'Female', 'Non-binary', 'Prefer not to say']
const SIZES   = ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL']
const SKIN_TONES = [
  { label: 'Very Light',   value: 'very_light',  hex: '#FDDBB4' },
  { label: 'Light',        value: 'light',        hex: '#F5C38D' },
  { label: 'Medium Light', value: 'medium_light', hex: '#D4A574' },
  { label: 'Medium',       value: 'medium',       hex: '#B8834A' },
  { label: 'Medium Dark',  value: 'medium_dark',  hex: '#8B5A2B' },
  { label: 'Dark',         value: 'dark',         hex: '#4A2F1A' },
]

// Body type options with SVG icon paths — vary by gender
const BODY_TYPES_MALE = [
  {
    value: 'slim',
    label: 'Slim',
    desc: 'Narrow frame, lean',
    // Rectangle — thin
    svg: `<rect x="9" y="2" width="6" height="20" rx="2" fill="currentColor" opacity="0.15"/>
          <rect x="10" y="2" width="4" height="4" rx="2" fill="currentColor"/>
          <path d="M9 6h6v8H9z" fill="currentColor" opacity="0.7"/>
          <path d="M9 14h2v8h2v-8h2" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>`,
  },
  {
    value: 'athletic',
    label: 'Athletic',
    desc: 'V-shape, broad shoulders',
    svg: `<path d="M7 8h10" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"/>
          <path d="M9 8v6h6V8" fill="currentColor" opacity="0.15"/>
          <path d="M9 14l-1 8h8l-1-8" fill="currentColor" opacity="0.5"/>
          <circle cx="12" cy="4" r="3" fill="currentColor"/>`,
  },
  {
    value: 'average',
    label: 'Average',
    desc: 'Balanced proportions',
    svg: `<circle cx="12" cy="4" r="3" fill="currentColor"/>
          <rect x="8" y="7" width="8" height="9" rx="1.5" fill="currentColor" opacity="0.6"/>
          <path d="M9 16l-1.5 6h9l-1.5-6" fill="currentColor" opacity="0.4"/>`,
  },
  {
    value: 'stocky',
    label: 'Stocky',
    desc: 'Broad, compact build',
    svg: `<circle cx="12" cy="4" r="3" fill="currentColor"/>
          <rect x="7" y="7" width="10" height="9" rx="2" fill="currentColor" opacity="0.7"/>
          <path d="M8 16l-1.5 6h11l-1.5-6" fill="currentColor" opacity="0.5"/>`,
  },
  {
    value: 'heavy',
    label: 'Heavy',
    desc: 'Fuller, rounded frame',
    svg: `<circle cx="12" cy="4" r="3" fill="currentColor"/>
          <ellipse cx="12" cy="13" rx="6" ry="7" fill="currentColor" opacity="0.6"/>
          <path d="M8 18l-1 4h10l-1-4" fill="currentColor" opacity="0.4"/>`,
  },
]

const BODY_TYPES_FEMALE = [
  {
    value: 'hourglass',
    label: 'Hourglass',
    desc: 'Equal bust & hips, defined waist',
    svg: `<circle cx="12" cy="4" r="3" fill="currentColor"/>
          <path d="M7 8c0 0 2 2 5 2s5-2 5-2v4c0 0-2 2-5 2s-5-2-5-2V8z" fill="currentColor" opacity="0.5"/>
          <path d="M7 14c0 0 2-1 5-1s5 1 5 1v4c0 0-2 2-5 2s-5-2-5-2v-4z" fill="currentColor" opacity="0.7"/>`,
  },
  {
    value: 'pear',
    label: 'Pear',
    desc: 'Fuller hips, narrower bust',
    svg: `<circle cx="12" cy="4" r="3" fill="currentColor"/>
          <path d="M9 8h6v5H9z" fill="currentColor" opacity="0.4"/>
          <ellipse cx="12" cy="18" rx="6" ry="5" fill="currentColor" opacity="0.7"/>`,
  },
  {
    value: 'apple',
    label: 'Apple',
    desc: 'Fuller midsection, narrow hips',
    svg: `<circle cx="12" cy="4" r="3" fill="currentColor"/>
          <ellipse cx="12" cy="13" rx="6" ry="6" fill="currentColor" opacity="0.6"/>
          <path d="M10 19h4v3h-4z" fill="currentColor" opacity="0.4"/>`,
  },
  {
    value: 'rectangle',
    label: 'Rectangle',
    desc: 'Straight, similar proportions',
    svg: `<circle cx="12" cy="4" r="3" fill="currentColor"/>
          <rect x="9" y="7" width="6" height="15" rx="1.5" fill="currentColor" opacity="0.5"/>`,
  },
  {
    value: 'athletic',
    label: 'Athletic',
    desc: 'Toned, broad shoulders',
    svg: `<circle cx="12" cy="4" r="3" fill="currentColor"/>
          <path d="M7 8h10v5c0 2-2 3-5 3s-5-1-5-3V8z" fill="currentColor" opacity="0.6"/>
          <path d="M9 16l-1 6h8l-1-6" fill="currentColor" opacity="0.4"/>`,
  },
]

const BODY_TYPES_OTHER = [
  { value: 'lean',     label: 'Lean',     desc: 'Slender, minimal mass' },
  { value: 'athletic', label: 'Athletic', desc: 'Toned and defined' },
  { value: 'average',  label: 'Average',  desc: 'Balanced proportions' },
  { value: 'full',     label: 'Full',     desc: 'Fuller, rounded curves' },
  { value: 'heavy',    label: 'Heavy',    desc: 'Heavier, broader frame' },
]

const bodyTypeOptions = computed(() => {
  const g = profile.gender.toLowerCase()
  if (g === 'male') return BODY_TYPES_MALE
  if (g === 'female') return BODY_TYPES_FEMALE
  return BODY_TYPES_OTHER.map(bt => ({ ...bt, svg: '' }))
})

const profileValid = computed(() =>
  profile.gender && profile.age && profile.height_cm &&
  profile.weight_kg && profile.usual_size && profile.skin_tone
)

async function saveProfile() {
  try {
    await userService.updateProfile({
      gender: profile.gender,
      age: profile.age ?? undefined,
      height_cm: profile.height_cm ?? undefined,
      weight_kg: profile.weight_kg ?? undefined,
      usual_size: profile.usual_size,
      skin_tone: profile.skin_tone,
    })
    step.value = 'upload'
  } catch {
    uiStore.toast('Failed to save profile. Please try again.', 'error')
  }
}

// ── Guided upload ─────────────────────────────────────────────────────────────
const slotInputRefs = reactive<Record<string, HTMLInputElement | null>>({})
const uploadedPhotoIds = ref<string[]>([])
const angleImages = ref<{ key: string; image_url: string }[]>([])
const detectedBodyType = ref('')
const candidates = ref<{ key: string; image_url: string }[]>([])
const selectedCandidate = ref<{ key: string; image_url: string } | null>(null)

function triggerSlotInput(type: GuidedPhotoType) {
  slotInputRefs[type]?.click()
}

function handleSlotInput(event: Event, type: GuidedPhotoType) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) setSlotFile(type, file)
  input.value = ''
}

const ANGLE_LABELS = [
  'Front', '¾ Left', '¾ Right', 'Left Profile', 'Right Profile',
  'Rear', 'Walking', 'Seated', 'Confident',
]

// Which slot is showing tips popover
const activeTipsSlot = ref<string | null>(null)

function startGeneratingMessages() {
  const messages = [
    { delay: 0,     text: 'Upscaling your photos for maximum detail...' },
    { delay: 6000,  text: 'Analyzing your body type...' },
    { delay: 18000, text: 'Generating 8 camera angle views with Gemini...' },
    { delay: 55000, text: 'Creating your AI try-on portraits...' },
    { delay: 85000, text: 'Almost done...' },
  ]
  messages.forEach(({ delay, text }) => {
    setTimeout(() => {
      if (step.value === 'generating') generatingMessage.value = text
    }, delay)
  })
}

async function uploadAndGenerate() {
  step.value = 'generating'
  generatingMessage.value = 'Uploading your photos...'
  startGeneratingMessages()

  try {
    // Upload all 5 photos IN ORDER — backend pipeline depends on this order
    const ids: string[] = []
    for (const slot of slots.value) {
      if (!slot.file) throw new Error(`Missing photo: ${slot.label}`)
      const photo = await userStore.uploadPhoto(slot.file.file, slot.type)
      ids.push(photo.id)
    }
    uploadedPhotoIds.value = ids

    // Full pipeline — returns body_type + angles + candidates
    const result = await userStore.generateIdentityCandidates(ids)

    detectedBodyType.value = result.body_type
    angleImages.value = result.angles
    candidates.value = result.candidates

    if (candidates.value.length === 0) throw new Error('No candidates generated')

    step.value = 'angles'
  } catch (err: any) {
    uiStore.toast(err?.response?.data?.detail || 'Generation failed. Please try again.', 'error')
    step.value = 'upload'
  }
}

function proceedToPick() {
  step.value = 'pick'
}

function selectCandidate(c: { key: string; image_url: string }) {
  selectedCandidate.value = c
}

async function confirmSelection() {
  if (!selectedCandidate.value) return
  try {
    await userStore.confirmIdentity(selectedCandidate.value.key, uploadedPhotoIds.value)
    step.value = 'done'
  } catch (err: any) {
    uiStore.toast(err?.response?.data?.detail || 'Failed to save identity.', 'error')
  }
}

// ── Progress ──────────────────────────────────────────────────────────────────
const STEPS: Step[] = ['profile', 'upload', 'generating', 'angles', 'pick', 'done']
const STEP_LABELS: Record<Step, string> = {
  profile: 'Profile', upload: 'Photos', generating: 'AI', angles: 'Angles', pick: 'Pick', done: 'Done',
}

</script>

<template>
  <div class="min-h-screen">
    <AppHeader />

    <div class="page-container py-12 max-w-3xl mx-auto">

      <!-- Progress bar -->
      <div class="flex items-center gap-2 mb-10">
        <template v-for="(s, i) in STEPS" :key="s">
          <div class="flex items-center gap-2">
            <div
              class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold transition-all duration-300"
              :class="step === s
                ? 'bg-drape-gold text-drape-obsidian'
                : STEPS.indexOf(step) > i
                  ? 'bg-drape-gold/20 text-drape-gold'
                  : 'bg-[var(--color-border)] text-[var(--color-text-muted)]'"
            >{{ i + 1 }}</div>
            <span class="text-xs hidden sm:block"
              :class="step === s ? 'text-drape-gold font-medium' : 'text-[var(--color-text-muted)]'">
              {{ STEP_LABELS[s] }}
            </span>
          </div>
          <div v-if="i < STEPS.length - 1" class="flex-1 h-px bg-[var(--color-border)]" />
        </template>
      </div>

      <Transition name="fade" mode="out-in">

        <!-- ── Step 1: Profile ──────────────────────────────────────── -->
        <div v-if="step === 'profile'" key="profile" class="animate-fadeUp">
          <h1 class="font-display text-3xl font-semibold mb-2">Tell us about yourself</h1>
          <p class="text-[var(--color-text-muted)] mb-8">
            This personalises your AI model — accurate proportions, skin tone, and fit.
          </p>

          <div class="space-y-7">
            <!-- Gender -->
            <div>
              <label class="block text-sm font-medium mb-3">Gender</label>
              <div class="flex flex-wrap gap-2">
                <button v-for="g in GENDERS" :key="g"
                  class="px-4 py-2 rounded-full text-sm border transition-all duration-150"
                  :class="profile.gender === g
                    ? 'bg-drape-gold text-drape-obsidian border-drape-gold font-medium'
                    : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-drape-gold/50'"
                  @click="profile.gender = g"
                >{{ g }}</button>
              </div>
            </div>

            <!-- Age / Height / Weight -->
            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="block text-sm font-medium mb-1.5">Age</label>
                <input v-model.number="profile.age" type="number" min="13" max="99"
                  placeholder="25" class="input" />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1.5">Height (cm)</label>
                <input v-model.number="profile.height_cm" type="number" min="100" max="250"
                  placeholder="170" class="input" />
              </div>
              <div>
                <label class="block text-sm font-medium mb-1.5">Weight (kg)</label>
                <input v-model.number="profile.weight_kg" type="number" min="30" max="300"
                  placeholder="65" class="input" />
              </div>
            </div>

            <!-- Usual size -->
            <div>
              <label class="block text-sm font-medium mb-3">Usual clothing size</label>
              <div class="flex flex-wrap gap-2">
                <button v-for="sz in SIZES" :key="sz"
                  class="w-14 py-2 rounded-xl text-sm border font-medium transition-all duration-150"
                  :class="profile.usual_size === sz
                    ? 'bg-drape-gold text-drape-obsidian border-drape-gold'
                    : 'border-[var(--color-border)] text-[var(--color-text-muted)] hover:border-drape-gold/50'"
                  @click="profile.usual_size = sz"
                >{{ sz }}</button>
              </div>
            </div>

            <!-- Skin tone -->
            <div>
              <label class="block text-sm font-medium mb-3">Skin tone</label>
              <div class="flex flex-wrap gap-3">
                <button v-for="tone in SKIN_TONES" :key="tone.value"
                  class="flex flex-col items-center gap-1.5 group"
                  @click="profile.skin_tone = tone.value"
                >
                  <div
                    class="w-10 h-10 rounded-full border-2 transition-all duration-150"
                    :style="{ backgroundColor: tone.hex }"
                    :class="profile.skin_tone === tone.value
                      ? 'border-drape-gold scale-110 shadow-lg'
                      : 'border-transparent group-hover:border-drape-gold/40'"
                  />
                  <span class="text-[10px] text-[var(--color-text-muted)] leading-tight text-center w-12">
                    {{ tone.label }}
                  </span>
                </button>
              </div>
            </div>

            <!-- Body type (visual, gender-specific) -->
            <div v-if="profile.gender">
              <label class="block text-sm font-medium mb-1">Body type</label>
              <p class="text-xs text-[var(--color-text-muted)] mb-4">
                Don't worry — our AI will verify this from your photos automatically.
              </p>
              <div class="grid grid-cols-5 gap-3">
                <button
                  v-for="bt in bodyTypeOptions"
                  :key="bt.value"
                  class="flex flex-col items-center gap-2 p-3 rounded-2xl border-2 transition-all duration-150 group"
                  :class="profile.usual_size /* placeholder — body type not in profile form, AI detects it */
                    ? 'border-[var(--color-border)] hover:border-drape-gold/40'
                    : 'border-[var(--color-border)] hover:border-drape-gold/40'"
                  :title="bt.desc"
                >
                  <!-- SVG icon -->
                  <div class="w-10 h-14 text-[var(--color-text-muted)] group-hover:text-drape-gold transition-colors">
                    <svg v-if="bt.svg" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"
                      class="w-full h-full" v-html="bt.svg" />
                    <!-- Text fallback for non-binary -->
                    <div v-else class="w-full h-full flex items-center justify-center text-2xl">
                      🧍
                    </div>
                  </div>
                  <span class="text-[11px] font-medium text-center leading-tight">{{ bt.label }}</span>
                  <span class="text-[10px] text-[var(--color-text-muted)] text-center leading-tight hidden group-hover:block">{{ bt.desc }}</span>
                </button>
              </div>
              <p class="text-xs text-drape-gold mt-3 flex items-center gap-1.5">
                <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                  <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Gemini will detect your actual body type from your photos
              </p>
            </div>
          </div>

          <div class="mt-10">
            <DrapeButton
              variant="gold"
              size="lg"
              :disabled="!profileValid"
              class="w-full"
              @click="saveProfile"
            >
              Continue to photos →
            </DrapeButton>
          </div>
        </div>

        <!-- ── Step 2: Upload ──────────────────────────────────────── -->
        <div v-else-if="step === 'upload'" key="upload" class="animate-fadeUp">
          <h1 class="font-display text-3xl font-semibold mb-2">Upload your 5 photos</h1>
          <p class="text-[var(--color-text-muted)] mb-2">
            Our AI needs these exact 5 angles — in order — to build an accurate digital model of you.
          </p>

          <!-- Order explanation banner -->
          <div class="flex items-start gap-3 p-3 rounded-xl bg-drape-gold/10 border border-drape-gold/30 mb-8">
            <svg class="w-4 h-4 text-drape-gold mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <p class="text-xs text-drape-gold leading-relaxed">
              <strong>Photo 1 (face close-up) is the most important.</strong>
              It anchors your identity — the AI reads your exact face features from it.
              Upload all 5 in the order shown below.
            </p>
          </div>

          <div class="space-y-3 mb-8">
            <div v-for="(slot, index) in slots" :key="slot.type">
              <!-- Hidden file input -->
              <input
                :ref="el => slotInputRefs[slot.type] = el as HTMLInputElement"
                type="file"
                accept="image/*"
                class="hidden"
                @change="(e) => handleSlotInput(e, slot.type)"
              />

              <!-- Slot row -->
              <div
                class="flex gap-4 items-center p-3 rounded-2xl border-2 transition-all duration-200 cursor-pointer group"
                :class="slot.file?.error
                  ? 'border-red-400 bg-red-400/5'
                  : slot.file
                    ? 'border-drape-gold bg-drape-gold/5'
                    : 'border-dashed border-[var(--color-border)] hover:border-drape-gold/50 hover:bg-[var(--color-surface)]'"
                @click="triggerSlotInput(slot.type)"
              >
                <!-- Order number -->
                <div
                  class="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0 transition-all"
                  :class="slot.file && !slot.file.error
                    ? 'bg-drape-gold text-drape-obsidian'
                    : 'bg-[var(--color-border)] text-[var(--color-text-muted)]'"
                >
                  {{ slot.file && !slot.file.error ? '✓' : index + 1 }}
                </div>

                <!-- Preview thumbnail OR silhouette -->
                <div class="w-14 h-[4.5rem] rounded-xl overflow-hidden flex-shrink-0 bg-[var(--color-border)]">
                  <img
                    v-if="slot.file && !slot.file.error"
                    :src="slot.file.preview"
                    :alt="slot.label"
                    class="w-full h-full object-cover"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center">
                    <svg class="w-6 h-6 text-[var(--color-text-muted)] opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                      <path d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                </div>

                <!-- Label + description -->
                <div class="flex-1 min-w-0">
                  <div class="flex items-center gap-2">
                    <p class="text-sm font-semibold">{{ slot.label }}</p>
                    <span v-if="index === 0" class="text-[10px] bg-drape-gold text-drape-obsidian px-2 py-0.5 rounded-full font-bold">KEY</span>
                  </div>
                  <p class="text-xs text-[var(--color-text-muted)] mt-0.5">{{ slot.description }}</p>
                  <p v-if="slot.file?.error" class="text-xs text-red-500 mt-0.5">{{ slot.file.error }}</p>
                </div>

                <!-- Right actions -->
                <div class="flex items-center gap-2 flex-shrink-0" @click.stop>
                  <!-- Tips button -->
                  <button
                    class="text-[10px] text-[var(--color-text-muted)] hover:text-drape-gold border border-[var(--color-border)] hover:border-drape-gold/40 rounded-full px-2 py-1 transition-all"
                    @click.stop="activeTipsSlot = activeTipsSlot === slot.type ? null : slot.type"
                  >
                    Tips
                  </button>
                  <!-- Remove -->
                  <button
                    v-if="slot.file"
                    class="w-7 h-7 rounded-full bg-[var(--color-border)] hover:bg-red-400/20 hover:text-red-400 flex items-center justify-center text-xs transition-all"
                    @click.stop="clearSlot(slot.type)"
                  >✕</button>
                  <!-- Upload icon -->
                  <div v-else class="w-7 h-7 rounded-full border border-[var(--color-border)] flex items-center justify-center opacity-50 group-hover:opacity-100 group-hover:border-drape-gold/50 transition-all">
                    <svg class="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
                      <path d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </div>
                </div>
              </div>

              <!-- Tips panel -->
              <div
                v-if="activeTipsSlot === slot.type"
                class="ml-12 mt-1 p-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]"
              >
                <p class="text-xs font-semibold mb-2 text-drape-gold">Tips for "{{ slot.label }}"</p>
                <ul class="space-y-1">
                  <li v-for="tip in slot.tips" :key="tip" class="text-xs text-[var(--color-text-muted)] flex items-start gap-1.5">
                    <span class="text-drape-gold mt-0.5">•</span>
                    {{ tip }}
                  </li>
                </ul>
              </div>
            </div>
          </div>

          <!-- Progress -->
          <div class="flex items-center gap-3 mb-6">
            <div class="flex-1 h-1.5 rounded-full bg-[var(--color-border)] overflow-hidden">
              <div
                class="h-full bg-drape-gold rounded-full transition-all duration-500"
                :style="{ width: `${(filledCount / 5) * 100}%` }"
              />
            </div>
            <p class="text-sm text-[var(--color-text-muted)] flex-shrink-0">
              {{ filledCount }}/5 ready
            </p>
          </div>

          <DrapeButton
            variant="gold"
            size="lg"
            :disabled="!allSlotsFilled"
            class="w-full"
            @click="uploadAndGenerate"
          >
            Generate my digital model →
          </DrapeButton>
        </div>

        <!-- ── Step 3: Generating ───────────────────────────────────── -->
        <div v-else-if="step === 'generating'" key="generating" class="text-center py-16 animate-fadeUp">
          <div class="w-24 h-24 rounded-full bg-drape-gold/10 flex items-center justify-center mx-auto mb-8">
            <DrapeSpinner size="lg" />
          </div>
          <h2 class="font-display text-2xl font-semibold mb-3">{{ generatingMessage }}</h2>
          <p class="text-[var(--color-text-muted)] text-sm max-w-sm mx-auto">
            Gemini is upscaling your photos, detecting your body type, and generating 8 multi-camera-angle views.
            This takes about 90–120 seconds.
          </p>
          <div class="flex justify-center gap-2 mt-8">
            <span v-for="i in 3" :key="i"
              class="w-2 h-2 rounded-full bg-drape-gold animate-pulse"
              :style="`animation-delay: ${i * 0.25}s`"
            />
          </div>
        </div>

        <!-- ── Step 4: Angles gallery ───────────────────────────────── -->
        <div v-else-if="step === 'angles'" key="angles" class="animate-fadeUp">
          <div class="flex items-start justify-between mb-2">
            <div>
              <h1 class="font-display text-3xl font-semibold">Your AI angles</h1>
              <p class="text-[var(--color-text-muted)] mt-1">
                Gemini generated {{ angleImages.length }} camera angle views of you. These are used to create your try-on portraits.
              </p>
            </div>
            <!-- Detected body type badge -->
            <div v-if="detectedBodyType"
              class="flex-shrink-0 ml-4 px-4 py-2 rounded-2xl bg-drape-gold/10 border border-drape-gold/30 text-center"
            >
              <p class="text-[10px] text-drape-gold uppercase tracking-widest font-medium">Body type detected</p>
              <p class="text-sm font-semibold capitalize mt-0.5">{{ detectedBodyType }}</p>
            </div>
          </div>

          <!-- Angles grid -->
          <div class="grid grid-cols-3 sm:grid-cols-5 gap-3 mt-6 mb-8">
            <div
              v-for="(img, i) in angleImages"
              :key="img.key"
              class="flex flex-col gap-1.5"
            >
              <div class="aspect-[3/4] rounded-xl overflow-hidden bg-[var(--color-border)] group relative">
                <img
                  :src="img.image_url"
                  :alt="ANGLE_LABELS[i] || `Angle ${i + 1}`"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  loading="lazy"
                />
                <div class="absolute inset-0 bg-drape-obsidian/0 group-hover:bg-drape-obsidian/20 transition-all duration-200" />
                <!-- Angle number badge -->
                <div class="absolute top-1.5 left-1.5 w-5 h-5 rounded-full bg-drape-obsidian/60 text-white text-[10px] flex items-center justify-center font-bold">
                  {{ i + 1 }}
                </div>
              </div>
              <p class="text-[10px] text-center text-[var(--color-text-muted)] font-medium">
                {{ ANGLE_LABELS[i] || `View ${i + 1}` }}
              </p>
            </div>

            <!-- Skeleton placeholders if fewer than 9 came back -->
            <div
              v-for="i in Math.max(0, 9 - angleImages.length)"
              :key="`skel-${i}`"
              class="aspect-[3/4] rounded-xl bg-[var(--color-border)] animate-pulse"
            />
          </div>

          <DrapeButton variant="gold" size="lg" class="w-full" @click="proceedToPick">
            Choose your portrait →
          </DrapeButton>
        </div>

        <!-- ── Step 5: Pick portrait ────────────────────────────────── -->
        <div v-else-if="step === 'pick'" key="pick" class="animate-fadeUp">
          <h1 class="font-display text-3xl font-semibold mb-2">Choose your identity</h1>
          <p class="text-[var(--color-text-muted)] mb-8">
            Pick the portrait that looks most like you — this is how you'll appear in try-ons.
          </p>

          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-8">
            <div
              v-for="c in candidates"
              :key="c.key"
              class="cursor-pointer group relative"
              @click="selectCandidate(c)"
            >
              <div
                class="aspect-[3/4] rounded-2xl overflow-hidden border-2 transition-all duration-200"
                :class="selectedCandidate?.key === c.key
                  ? 'border-drape-gold shadow-lg shadow-drape-gold/20 scale-[1.02]'
                  : 'border-transparent hover:border-drape-gold/40'"
              >
                <img :src="c.image_url" alt="Portrait candidate"
                  class="w-full h-full object-cover" />
              </div>
              <!-- Selected check -->
              <div v-if="selectedCandidate?.key === c.key"
                class="absolute top-2 right-2 w-7 h-7 rounded-full bg-drape-gold text-drape-obsidian
                       flex items-center justify-center text-sm font-bold shadow"
              >✓</div>
            </div>
          </div>

          <div class="flex gap-3">
            <DrapeButton variant="ghost" class="flex-1" @click="step = 'angles'">
              ← Back
            </DrapeButton>
            <DrapeButton
              variant="gold"
              class="flex-1"
              :disabled="!selectedCandidate"
              @click="confirmSelection"
            >
              Use this identity →
            </DrapeButton>
          </div>
        </div>

        <!-- ── Step 6: Done ────────────────────────────────────────── -->
        <div v-else-if="step === 'done'" key="done" class="text-center py-16 animate-fadeUp">
          <div class="w-20 h-20 rounded-full bg-drape-gold/20 flex items-center justify-center mx-auto mb-6 text-3xl">
            ✨
          </div>
          <h2 class="font-display text-3xl font-semibold mb-3">You're all set!</h2>
          <p class="text-[var(--color-text-muted)] mb-2">Your AI identity is ready.</p>
          <p v-if="detectedBodyType" class="text-sm text-drape-gold mb-8">
            Body type detected: <span class="font-semibold capitalize">{{ detectedBodyType }}</span>
          </p>
          <div class="flex flex-col sm:flex-row gap-3 justify-center">
            <RouterLink to="/catalog">
              <DrapeButton variant="gold" size="lg">Start trying on →</DrapeButton>
            </RouterLink>
          </div>
        </div>

      </Transition>
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
