import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { tryonService } from '@/services/tryon.service'
import { useTryOnStore } from '@/stores/tryon'
import { useUserStore } from '@/stores/user'
import { useUIStore } from '@/stores/ui'
import type { TryOnStatus } from '@/types'

export function useTryOn() {
  const router = useRouter()
  const tryonStore = useTryOnStore()
  const userStore = useUserStore()
  const uiStore = useUIStore()

  const status = ref<TryOnStatus>('pending')
  const progress = ref(0)
  const resultUrl = ref<string | null>(null)
  const errorMessage = ref<string | null>(null)
  const jobId = ref<string | null>(null)

  let pollTimer: ReturnType<typeof setInterval> | null = null
  let progressTimer: ReturnType<typeof setInterval> | null = null

  function startFakeProgress() {
    progress.value = 0
    progressTimer = setInterval(() => {
      if (progress.value < 90) {
        // Ease out: fast at start, slow near 90%
        const remaining = 90 - progress.value
        progress.value += Math.max(0.5, remaining * 0.04)
      }
    }, 300)
  }

  function stopFakeProgress(complete = true) {
    if (progressTimer) clearInterval(progressTimer)
    if (complete) progress.value = 100
  }

  function startPolling() {
    pollTimer = setInterval(async () => {
      if (!jobId.value) return
      try {
        const update = await tryonService.getStatus(jobId.value)
        status.value = update.status
        tryonStore.updateJobStatus(update.status, update.result_url)

        if (update.status === 'completed') {
          resultUrl.value = update.result_url
          stopFakeProgress(true)
          stopPolling()
          router.push({ name: 'result', params: { jobId: jobId.value } })
        } else if (update.status === 'failed') {
          errorMessage.value = update.error_message || 'Try-on failed. Please try again.'
          stopFakeProgress(false)
          stopPolling()
          uiStore.toast(errorMessage.value, 'error')
        }
      } catch {
        // Ignore transient poll errors
      }
    }, 3000)
  }

  function stopPolling() {
    if (pollTimer) clearInterval(pollTimer)
    pollTimer = null
  }

  async function submitTryOn(productId: string) {
    const identity = userStore.identity
    if (!identity || identity.status !== 'completed') {
      uiStore.toast('Please complete your identity setup first', 'error')
      router.push({ name: 'onboarding' })
      return
    }

    status.value = 'processing'
    errorMessage.value = null
    startFakeProgress()

    try {
      const response = await tryonService.submit(productId, identity.id)
      jobId.value = response.job_id
      tryonStore.setActiveJob(response.job_id)
      startPolling()
    } catch (err: any) {
      status.value = 'failed'
      errorMessage.value = err?.response?.data?.detail || 'Failed to start try-on'
      stopFakeProgress(false)
      uiStore.toast(errorMessage.value!, 'error')
    }
  }

  function cancelTryOn() {
    stopPolling()
    stopFakeProgress(false)
    status.value = 'pending'
    progress.value = 0
  }

  onUnmounted(() => {
    stopPolling()
    if (progressTimer) clearInterval(progressTimer)
  })

  return { status, progress, resultUrl, errorMessage, jobId, submitTryOn, cancelTryOn }
}
