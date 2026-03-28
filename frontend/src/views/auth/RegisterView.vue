<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Register and login are the same flow with Google OAuth
onMounted(() => router.replace('/login'))
</script>

<template>
  <div />
</template>
