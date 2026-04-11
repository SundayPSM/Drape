import api from './api'
import type { User, UserPhoto, UserIdentity, ProfileUpdate } from '@/types'

export const userService = {
  async getMe(): Promise<User> {
    const { data } = await api.get<User>('/api/v1/users/me')
    return data
  },

  async updateProfile(data: ProfileUpdate): Promise<User> {
    const { data: user } = await api.patch<User>('/api/v1/users/me/profile', data)
    return user
  },

  async getMyPhotos(): Promise<UserPhoto[]> {
    const { data } = await api.get<UserPhoto[]>('/api/v1/users/me/photos')
    return data
  },

  async presignPhotoUpload(photoType: string): Promise<{ photo_id: string; key: string; presigned: any }> {
    const { data } = await api.post('/api/v1/users/me/photos/presign', null, {
      params: { photo_type: photoType },
    })
    return data
  },

  async uploadPhotoToStorage(presigned: any, file: File): Promise<void> {
    // Supabase Storage signed upload: PUT with raw file body
    const res = await fetch(presigned.url, {
      method: 'PUT',
      body: file,
      headers: { 'Content-Type': file.type || 'image/jpeg' },
    })
    if (!res.ok) throw new Error(`Upload failed: ${res.status}`)
  },

  async getMyIdentity(): Promise<UserIdentity | null> {
    const { data } = await api.get<UserIdentity | null>('/api/v1/users/me/identity')
    return data
  },

  async generateIdentityCandidates(photoIds: string[]): Promise<{
    body_type: string
    angles: { key: string; image_url: string }[]
    candidates: { key: string; image_url: string }[]
  }> {
    const { data } = await api.post('/api/v1/users/me/identity/generate', photoIds)
    return data
  },

  async confirmIdentity(s3Key: string, photoIds: string[]): Promise<UserIdentity> {
    const { data } = await api.post<UserIdentity>('/api/v1/users/me/identity/confirm', {
      s3_key: s3Key,
      photo_ids: photoIds,
    })
    return data
  },
}
