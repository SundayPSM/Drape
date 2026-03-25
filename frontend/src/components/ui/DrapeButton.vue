<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'ghost' | 'gold'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  type?: 'button' | 'submit' | 'reset'
}>()
</script>

<template>
  <button
    :type="type ?? 'button'"
    :disabled="disabled || loading"
    :class="[
      variant === 'gold' ? 'btn-gold' : variant === 'ghost' ? 'btn-ghost' : 'btn-primary',
      size === 'sm' ? '!px-4 !py-2 !text-xs' : size === 'lg' ? '!px-8 !py-4 !text-base' : '',
    ]"
  >
    <svg v-if="loading" class="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
    </svg>
    <slot />
  </button>
</template>
