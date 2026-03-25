import api from './api'
import type { TryOnStatusResponse, TryOnJob } from '@/types'

export const tryonService = {
  async submit(productId: string, identityId: string): Promise<TryOnStatusResponse> {
    const { data } = await api.post<TryOnStatusResponse>('/api/v1/tryon/submit', {
      product_id: productId,
      identity_id: identityId,
    })
    return data
  },

  async getStatus(jobId: string): Promise<TryOnStatusResponse> {
    const { data } = await api.get<TryOnStatusResponse>(`/api/v1/tryon/${jobId}/status`)
    return data
  },

  async getHistory(page = 1, pageSize = 20): Promise<TryOnJob[]> {
    const { data } = await api.get<TryOnJob[]>('/api/v1/tryon/history', {
      params: { page, page_size: pageSize },
    })
    return data
  },

  async saveLook(jobId: string): Promise<TryOnJob> {
    const { data } = await api.patch<TryOnJob>(`/api/v1/tryon/${jobId}/save`)
    return data
  },
}
