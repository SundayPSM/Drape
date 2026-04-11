export interface User {
  id: string
  email: string
  name: string
  avatar_url: string | null
  gender: string | null
  age: number | null
  height_cm: number | null
  weight_kg: number | null
  usual_size: string | null
  skin_tone: string | null
  body_type: string | null
  created_at: string
}

export interface GenerationResult {
  body_type: string
  angles: { key: string; image_url: string }[]
  candidates: { key: string; image_url: string }[]
}

export interface ProfileUpdate {
  gender?: string
  age?: number
  height_cm?: number
  weight_kg?: number
  usual_size?: string
  skin_tone?: string
}

export interface UserPhoto {
  id: string
  s3_key: string
  photo_type: 'front' | 'side' | 'full_body' | 'general'
  sort_order: number
  url: string | null
}

export interface UserIdentity {
  id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  image_url: string | null
  is_active: boolean
  created_at: string
}

export interface Product {
  id: string
  name: string
  brand: string | null
  description: string | null
  category: ProductCategory
  price: number | null
  currency: string
  image_url: string | null
  source_url: string | null
  affiliate_url: string | null
  is_curated: boolean
  created_at: string
}

export type ProductCategory =
  | 'tops'
  | 'bottoms'
  | 'dresses'
  | 'outerwear'
  | 'footwear'
  | 'accessories'
  | 'watches'
  | 'sunglasses'

export type TryOnFit = 'slim' | 'regular' | 'oversized'
export type TryOnStatus = 'pending' | 'processing' | 'completed' | 'failed'

export interface TryOnJob {
  id: string
  status: TryOnStatus
  product: Product | null
  result_url: string | null
  human_img_url: string | null
  is_saved: boolean
  share_slug: string | null
  created_at: string
  completed_at: string | null
}

export interface TryOnStatusResponse {
  job_id: string
  status: TryOnStatus
  result_url: string | null
  error_message: string | null
}

export interface ApiError {
  detail: string
}

export interface ProductListResponse {
  items: Product[]
  total: number
  page: number
  page_size: number
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
}
