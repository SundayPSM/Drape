<script setup lang="ts">
defineProps<{ size?: 'sm' | 'md' | 'lg' }>()
</script>

<template>
  <div
    :class="[
      'rounded-full border-2 border-drape-gold/20 border-t-drape-gold animate-spin',
      size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-10 h-10' : 'w-6 h-6',
    ]"
  />
</template>
