<script setup lang="ts">
import { useUIStore } from '@/stores/ui'
const uiStore = useUIStore()
</script>

<template>
  <button
    class="relative w-10 h-10 rounded-full flex items-center justify-center
           text-[var(--color-text-muted)] hover:text-[var(--color-text)]
           hover:bg-[var(--color-border)] transition-all duration-200"
    :title="uiStore.isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    @click="uiStore.toggleTheme"
  >
    <Transition
      enter-active-class="transition-all duration-200"
      enter-from-class="opacity-0 rotate-90 scale-50"
      enter-to-class="opacity-100 rotate-0 scale-100"
      leave-active-class="transition-all duration-150"
      leave-from-class="opacity-100 rotate-0 scale-100"
      leave-to-class="opacity-0 -rotate-90 scale-50"
      mode="out-in"
    >
      <!-- Sun icon -->
      <svg v-if="uiStore.isDark" key="sun" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41" stroke-linecap="round" />
      </svg>
      <!-- Moon icon -->
      <svg v-else key="moon" xmlns="http://www.w3.org/2000/svg" width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
        <path d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z" stroke-linecap="round" stroke-linejoin="round" />
      </svg>
    </Transition>
  </button>
</template>
