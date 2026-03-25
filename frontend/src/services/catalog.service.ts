import api from './api'
import type { Product, ProductListResponse, ProductCategory } from '@/types'

export const catalogService = {
  async listProducts(params: {
    category?: ProductCategory
    q?: string
    page?: number
    page_size?: number
  } = {}): Promise<ProductListResponse> {
    const { data } = await api.get<ProductListResponse>('/api/v1/products', { params })
    return data
  },

  async getProduct(id: string): Promise<Product> {
    const { data } = await api.get<Product>(`/api/v1/products/${id}`)
    return data
  },

  async scrapeProduct(url: string): Promise<Product> {
    const { data } = await api.post<Product>('/api/v1/products/scrape', { url })
    return data
  },
}
