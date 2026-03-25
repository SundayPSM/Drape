<script setup lang="ts">
defineProps<{ class?: string }>()
</script>

<template>
  <div
    :class="['skeleton bg-[var(--color-border)] animate-pulse rounded-xl', $props.class]"
    style="background: linear-gradient(90deg, var(--color-border) 25%, rgba(201,169,110,0.06) 50%, var(--color-border) 75%); background-size: 200% 100%; animation: shimmer 1.8s ease-in-out infinite;"
  />
</template>
