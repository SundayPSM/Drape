import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export interface Toast {
  id: string
  type: 'success' | 'error' | 'info'
  message: string
}

export const useUIStore = defineStore('ui', () => {
  const isDark = ref(false)
  const toasts = ref<Toast[]>([])

  function initTheme() {
    const stored = localStorage.getItem('theme')
    isDark.value = stored
      ? stored === 'dark'
      : window.matchMedia('(prefers-color-scheme: dark)').matches
    applyTheme()
  }

  function toggleTheme() {
    isDark.value = !isDark.value
    localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
    applyTheme()
  }

  function applyTheme() {
    document.documentElement.classList.toggle('dark', isDark.value)
  }

  function toast(message: string, type: Toast['type'] = 'info') {
    const id = crypto.randomUUID()
    toasts.value.push({ id, type, message })
    setTimeout(() => dismissToast(id), 4000)
  }

  function dismissToast(id: string) {
    toasts.value = toasts.value.filter((t) => t.id !== id)
  }

  return { isDark, toasts, initTheme, toggleTheme, toast, dismissToast }
})
