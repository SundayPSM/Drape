<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps<{
  beforeUrl: string
  afterUrl: string
  beforeLabel?: string
  afterLabel?: string
}>()

const sliderPosition = ref(50) // 0-100
const container = ref<HTMLElement | null>(null)
const dragging = ref(false)

function getPositionFromEvent(e: PointerEvent): number {
  if (!container.value) return 50
  const rect = container.value.getBoundingClientRect()
  const x = e.clientX - rect.left
  return Math.min(100, Math.max(0, (x / rect.width) * 100))
}

function onPointerDown(e: PointerEvent) {
  dragging.value = true
  ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  sliderPosition.value = getPositionFromEvent(e)
}

function onPointerMove(e: PointerEvent) {
  if (!dragging.value) return
  sliderPosition.value = getPositionFromEvent(e)
}

function onPointerUp() {
  dragging.value = false
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === 'ArrowLeft') sliderPosition.value = Math.max(0, sliderPosition.value - 2)
  if (e.key === 'ArrowRight') sliderPosition.value = Math.min(100, sliderPosition.value + 2)
}

// Hint animation on mount
onMounted(() => {
  setTimeout(() => {
    let dir = 1
    let count = 0
    const interval = setInterval(() => {
      sliderPosition.value += dir * 1.5
      count++
      if (count >= 8) dir = -1
      if (count >= 16) clearInterval(interval)
    }, 30)
  }, 800)
})
</script>

<template>
  <div
    ref="container"
    class="relative w-full overflow-hidden rounded-2xl select-none cursor-col-resize"
    :class="dragging ? 'cursor-grabbing' : 'cursor-col-resize'"
    tabindex="0"
    role="slider"
    :aria-valuenow="Math.round(sliderPosition)"
    aria-valuemin="0"
    aria-valuemax="100"
    aria-label="Before and after comparison"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @keydown="onKeyDown"
  >
    <!-- Before image (full width) -->
    <div class="w-full aspect-[3/4]">
      <img :src="beforeUrl" alt="Before" class="w-full h-full object-cover" draggable="false" />
    </div>

    <!-- After image (clipped by slider) -->
    <div
      class="absolute inset-0 overflow-hidden"
      :style="`clip-path: inset(0 ${100 - sliderPosition}% 0 0)`"
    >
      <img :src="afterUrl" alt="After" class="w-full h-full object-cover" draggable="false" />
    </div>

    <!-- Divider line -->
    <div
      class="absolute top-0 bottom-0 w-0.5 bg-white shadow-lg z-10 pointer-events-none"
      :style="`left: ${sliderPosition}%`"
    >
      <!-- Handle -->
      <div class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10
                  rounded-full bg-white shadow-xl flex items-center justify-center">
        <svg class="w-5 h-5 text-drape-obsidian" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
          <path d="M8 9l-3 3 3 3M16 9l3 3-3 3" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>
    </div>

    <!-- Labels -->
    <div class="absolute bottom-4 left-4 bg-drape-obsidian/70 text-drape-cream text-xs font-medium px-3 py-1 rounded-full backdrop-blur-sm pointer-events-none">
      {{ beforeLabel ?? 'Original' }}
    </div>
    <div class="absolute bottom-4 right-4 bg-drape-gold text-drape-obsidian text-xs font-medium px-3 py-1 rounded-full pointer-events-none">
      {{ afterLabel ?? 'With Drape' }}
    </div>
  </div>
</template>
