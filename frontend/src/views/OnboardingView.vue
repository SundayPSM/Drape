<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useUIStore } from '@/stores/ui'
import DrapeButton from '@/components/ui/DrapeButton.vue'
import DrapeSpinner from '@/components/ui/DrapeSpinner.vue'
import AppHeader from '@/components/layout/AppHeader.vue'
import type { UploadFile } from '@/composables/useFileUpload'
import { useFileUpload } from '@/composables/useFileUpload'

const router = useRouter()
const userStore = useUserStore()
const uiStore = useUIStore()
const { files, isDragging, addFiles, removeFile, handleDrop, handleDragOver, handleDragLeave } = useFileUpload()

const step = ref<'upload' | 'generating' | 'confirm'>('upload')
const generating = ref(false)
const generatedIdentity = ref<any>(null)

const photoTypes: UploadFile['type'][] = ['front', 'side', 'full_body', 'general']
const photoLabels = {
  front: 'Front view',
  side: 'Side view',
  full_body: 'Full body',
  general: 'Additional',
}

const validFiles = computed(() => files.value.filter((f) => !f.error))
const canProceed = computed(() => validFiles.value.length >= 4)

function handleFileInput(event: Event) {
  const input = event.target as HTMLInputElement
  if (input.files) addFiles(input.files)
}

async function uploadAndGenerate() {
  generating.value = true
  step.value = 'generating'
  try {
    const uploadedIds: string[] = []
    for (const f of validFiles.value) {
      const photo = await userStore.uploadPhoto(f.file, f.type)
      uploadedIds.push(photo.id)
    }
    await userStore.generateIdentity(uploadedIds)
    generatedIdentity.value = userStore.identity
    step.value = 'confirm'
  } catch (err: any) {
    uiStore.toast(err?.response?.data?.detail || 'Failed to generate identity', 'error')
    step.value = 'upload'
  } finally {
    generating.value = false
  }
}

function proceed() {
  router.push('/catalog')
}
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />

    <div class="page-container py-12 max-w-2xl mx-auto">
      <!-- Progress indicator -->
      <div class="flex items-center gap-3 mb-10">
        <div
          v-for="(s, i) in ['upload', 'generating', 'confirm']"
          :key="s"
          class="flex items-center gap-3"
        >
          <div
            class="w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold transition-all duration-300"
            :class="step === s
              ? 'bg-drape-gold text-drape-obsidian'
              : ['upload', 'generating', 'confirm'].indexOf(step) > i
                ? 'bg-drape-gold/20 text-drape-gold'
                : 'bg-[var(--color-border)] text-[var(--color-text-muted)]'"
          >
            {{ i + 1 }}
          </div>
          <div v-if="i < 2" class="flex-1 h-px bg-[var(--color-border)] w-8" />
        </div>
      </div>

      <!-- Step 1: Upload -->
      <Transition name="fade" mode="out-in">
        <div v-if="step === 'upload'" key="upload" class="animate-fadeUp">
          <h1 class="font-display text-3xl font-semibold mb-2">Upload your photos</h1>
          <p class="text-[var(--color-text-muted)] mb-8">
            Upload at least 4 clear photos of yourself. The better the photos, the more realistic your try-on.
          </p>

          <!-- Drop zone -->
          <div
            class="border-2 border-dashed rounded-2xl p-10 text-center transition-all duration-200 cursor-pointer mb-6"
            :class="isDragging
              ? 'border-drape-gold bg-drape-gold/5'
              : 'border-[var(--color-border)] hover:border-drape-gold/50'"
            @drop.prevent="handleDrop"
            @dragover.prevent="handleDragOver"
            @dragleave="handleDragLeave"
            @click="($refs.fileInput as HTMLInputElement).click()"
          >
            <div class="text-4xl mb-4">📸</div>
            <p class="font-medium mb-1">Drop photos here or click to upload</p>
            <p class="text-sm text-[var(--color-text-muted)]">JPEG, PNG or WebP · Max 20MB each</p>
            <input ref="fileInput" type="file" multiple accept="image/*" class="hidden" @change="handleFileInput" />
          </div>

          <!-- Photo grid -->
          <div v-if="files.length > 0" class="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            <div
              v-for="f in files"
              :key="f.id"
              class="relative aspect-square rounded-xl overflow-hidden group"
            >
              <img :src="f.preview" :alt="f.type" class="w-full h-full object-cover" />
              <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                <button
                  class="text-white text-xs font-medium bg-red-500/80 px-3 py-1 rounded-full"
                  @click.stop="removeFile(f.id)"
                >
                  Remove
                </button>
              </div>
              <div v-if="f.error" class="absolute bottom-0 left-0 right-0 bg-red-500/80 text-white text-xs p-1 text-center">
                {{ f.error }}
              </div>
              <div class="absolute top-2 left-2 bg-drape-obsidian/60 text-drape-cream text-xs px-2 py-0.5 rounded-full">
                {{ photoLabels[f.type] }}
              </div>
            </div>
          </div>

          <p class="text-sm text-[var(--color-text-muted)] mb-6">
            {{ validFiles.length }}/4 required photos uploaded
          </p>

          <DrapeButton
            variant="gold"
            size="lg"
            :disabled="!canProceed"
            class="w-full"
            @click="uploadAndGenerate"
          >
            Generate my identity →
          </DrapeButton>
        </div>

        <!-- Step 2: Generating -->
        <div v-else-if="step === 'generating'" key="generating" class="text-center py-16 animate-fadeUp">
          <div class="w-20 h-20 rounded-full bg-drape-gold/10 flex items-center justify-center mx-auto mb-8">
            <DrapeSpinner size="lg" />
          </div>
          <h2 class="font-display text-2xl font-semibold mb-3">Creating your digital identity</h2>
          <p class="text-[var(--color-text-muted)]">
            Our AI is analyzing your photos and building your personalized model...
          </p>
          <div class="flex justify-center gap-1 mt-6">
            <span v-for="i in 3" :key="i" class="w-2 h-2 rounded-full bg-drape-gold animate-pulse" :style="`animation-delay: ${i * 0.2}s`" />
          </div>
        </div>

        <!-- Step 3: Confirm -->
        <div v-else-if="step === 'confirm'" key="confirm" class="animate-fadeUp">
          <h1 class="font-display text-3xl font-semibold mb-2">Your identity is ready</h1>
          <p class="text-[var(--color-text-muted)] mb-8">
            This is how you'll appear in virtual try-ons. Happy with it?
          </p>

          <div class="card p-4 mb-8 max-w-xs mx-auto">
            <img
              v-if="generatedIdentity?.image_url"
              :src="generatedIdentity.image_url"
              alt="Your AI identity"
              class="w-full rounded-xl aspect-[3/4] object-cover"
            />
            <div v-else class="aspect-[3/4] rounded-xl bg-drape-gold/10 flex items-center justify-center">
              <span class="text-4xl">👤</span>
            </div>
          </div>

          <div class="flex gap-3">
            <DrapeButton variant="ghost" class="flex-1" @click="step = 'upload'">
              Retake photos
            </DrapeButton>
            <DrapeButton variant="gold" class="flex-1" @click="proceed">
              Start trying on →
            </DrapeButton>
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
