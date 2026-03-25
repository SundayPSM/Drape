import api from './api'
import type { User, UserPhoto, UserIdentity } from '@/types'

export const userService = {
  async getMe(): Promise<User> {
    const { data } = await api.get<User>('/api/v1/users/me')
    return data
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

  async uploadPhotoToS3(presigned: any, file: File): Promise<void> {
    const formData = new FormData()
    Object.entries(presigned.fields as Record<string, string>).forEach(([k, v]) => {
      formData.append(k, v)
    })
    formData.append('file', file)
    await fetch(presigned.url, { method: 'POST', body: formData })
  },

  async getMyIdentity(): Promise<UserIdentity | null> {
    const { data } = await api.get<UserIdentity | null>('/api/v1/users/me/identity')
    return data
  },

  async generateIdentity(photoIds: string[]): Promise<UserIdentity> {
    const { data } = await api.post<UserIdentity>('/api/v1/users/me/identity/generate', photoIds)
    return data
  },
}
