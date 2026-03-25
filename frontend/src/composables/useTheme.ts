import { useUIStore } from '@/stores/ui'

export function useTheme() {
  const uiStore = useUIStore()
  return {
    isDark: () => uiStore.isDark,
    toggle: uiStore.toggleTheme,
  }
}
