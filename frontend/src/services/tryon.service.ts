import api from './api'
import type { TryOnStatusResponse, TryOnJob, TryOnFit, ProductCategory } from '@/types'

interface ExtraGarment {
  image_url: string
  source_url: string
  category: ProductCategory
  name?: string
  fit: TryOnFit
}

export const tryonService = {
  async submit(productId: string, identityId: string, fit: TryOnFit = 'regular'): Promise<TryOnStatusResponse> {
    const { data } = await api.post<TryOnStatusResponse>('/api/v1/tryon/submit', {
      product_id: productId,
      identity_id: identityId,
      fit,
    })
    return data
  },

  async submitOutfit(
    productId: string,
    identityId: string,
    fit: TryOnFit = 'regular',
    extraGarments: ExtraGarment[] = [],
    poseImageUrl: string | null = null,
    baseImageUrl: string | null = null,
  ): Promise<TryOnStatusResponse> {
    const { data } = await api.post<TryOnStatusResponse>('/api/v1/tryon/submit', {
      product_id: productId,
      identity_id: identityId,
      fit,
      extra_garments: extraGarments,
      pose_image_url: poseImageUrl || undefined,
      base_image_url: baseImageUrl || undefined,
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
