import { useUIStore } from '@/stores/ui'

export function useShare() {
  const uiStore = useUIStore()

  async function share(title: string, text: string, url: string) {
    if (navigator.share) {
      try {
        await navigator.share({ title, text, url })
        return true
      } catch {
        // User cancelled or browser doesn't support
      }
    }
    // Fallback: copy to clipboard
    try {
      await navigator.clipboard.writeText(url)
      uiStore.toast('Link copied to clipboard!', 'success')
      return true
    } catch {
      uiStore.toast('Could not copy link', 'error')
      return false
    }
  }

  return { share }
}
