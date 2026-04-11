import api from './api'
import type { Product, ProductCategory } from '@/types'

export const productService = {
  async extractImage(url: string): Promise<{ image_url: string; title: string | null; source_url: string }> {
    const { data } = await api.post('/api/v1/products/extract-image', { url })
    return data
  },

  async quickAdd(payload: {
    image_url: string
    source_url: string
    category: ProductCategory
    name?: string
  }): Promise<Product> {
    const { data } = await api.post<Product>('/api/v1/products/quick-add', payload)
    return data
  },
}
