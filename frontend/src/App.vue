<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useUIStore } from '@/stores/ui'
import DrapeToast from '@/components/ui/DrapeToast.vue'

const authStore = useAuthStore()
const uiStore = useUIStore()

onMounted(async () => {
  uiStore.initTheme()
  await authStore.init()
})
</script>

<template>
  <RouterView />
  <DrapeToast />
</template>
