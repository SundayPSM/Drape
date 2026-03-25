<script setup lang="ts">
import { useUIStore } from '@/stores/ui'

const uiStore = useUIStore()
</script>

<template>
  <Teleport to="body">
    <div class="fixed bottom-6 right-6 z-50 flex flex-col gap-3 pointer-events-none">
      <TransitionGroup
        enter-active-class="transition-all duration-300 ease-out"
        enter-from-class="opacity-0 translate-y-4 scale-95"
        enter-to-class="opacity-100 translate-y-0 scale-100"
        leave-active-class="transition-all duration-200 ease-in"
        leave-from-class="opacity-100 translate-y-0 scale-100"
        leave-to-class="opacity-0 translate-y-2 scale-95"
      >
        <div
          v-for="toast in uiStore.toasts"
          :key="toast.id"
          class="pointer-events-auto flex items-center gap-3 px-5 py-3.5 rounded-2xl shadow-xl
                 backdrop-blur-sm border text-sm font-medium max-w-sm"
          :class="{
            'bg-drape-obsidian/90 dark:bg-drape-charcoal/90 border-drape-charcoal-light text-drape-cream': toast.type === 'info',
            'bg-green-950/90 border-green-800 text-green-300': toast.type === 'success',
            'bg-red-950/90 border-red-800 text-red-300': toast.type === 'error',
          }"
        >
          <span v-if="toast.type === 'success'">✓</span>
          <span v-else-if="toast.type === 'error'">✕</span>
          <span v-else>◆</span>
          {{ toast.message }}
          <button
            class="ml-auto opacity-60 hover:opacity-100 transition-opacity"
            @click="uiStore.dismissToast(toast.id)"
          >
            ✕
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>
