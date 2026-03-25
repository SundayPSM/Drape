import { defineStore } from 'pinia'
import { ref } from 'vue'
import { userService } from '@/services/user.service'
import type { UserPhoto, UserIdentity } from '@/types'

export const useUserStore = defineStore('user', () => {
  const photos = ref<UserPhoto[]>([])
  const identity = ref<UserIdentity | null>(null)
  const uploadingPhotos = ref(false)

  async function loadPhotos() {
    photos.value = await userService.getMyPhotos()
  }

  async function loadIdentity() {
    identity.value = await userService.getMyIdentity()
  }

  async function uploadPhoto(file: File, photoType: string = 'general'): Promise<UserPhoto> {
    const presignData = await userService.presignPhotoUpload(photoType)
    await userService.uploadPhotoToS3(presignData.presigned, file)
    await loadPhotos()
    return photos.value.find((p) => p.id === presignData.photo_id)!
  }

  async function generateIdentity(photoIds: string[]) {
    identity.value = await userService.generateIdentity(photoIds)
  }

  const hasEnoughPhotos = () => photos.value.length >= 4
  const hasIdentity = () => identity.value?.status === 'completed'

  return {
    photos,
    identity,
    uploadingPhotos,
    loadPhotos,
    loadIdentity,
    uploadPhoto,
    generateIdentity,
    hasEnoughPhotos,
    hasIdentity,
  }
})
