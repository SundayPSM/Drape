import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { tryonService } from '@/services/tryon.service'
import type { Product, TryOnJob, TryOnStatus } from '@/types'

export const useTryOnStore = defineStore('tryon', () => {
  const selectedProduct = ref<Product | null>(null)
  const activeJobId = ref<string | null>(null)
  const activeStatus = ref<TryOnStatus>('pending')
  const resultUrl = ref<string | null>(null)
  const history = ref<TryOnJob[]>([])
  const loading = ref(false)

  const savedLooks = computed(() => history.value.filter((j) => j.is_saved))
  const completedJobs = computed(() => history.value.filter((j) => j.status === 'completed'))

  function selectProduct(product: Product) {
    selectedProduct.value = product
  }

  async function loadHistory() {
    history.value = await tryonService.getHistory()
  }

  async function saveLook(jobId: string) {
    const updated = await tryonService.saveLook(jobId)
    const idx = history.value.findIndex((j) => j.id === jobId)
    if (idx !== -1) history.value[idx] = updated
  }

  function setActiveJob(jobId: string) {
    activeJobId.value = jobId
    activeStatus.value = 'processing'
    resultUrl.value = null
  }

  function updateJobStatus(status: TryOnStatus, url: string | null = null) {
    activeStatus.value = status
    if (url) resultUrl.value = url
  }

  return {
    selectedProduct,
    activeJobId,
    activeStatus,
    resultUrl,
    history,
    loading,
    savedLooks,
    completedJobs,
    selectProduct,
    loadHistory,
    saveLook,
    setActiveJob,
    updateJobStatus,
  }
})
