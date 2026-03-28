<script setup lang="ts">
import AppHeader from '@/components/layout/AppHeader.vue'
import DrapeButton from '@/components/ui/DrapeButton.vue'
</script>

<template>
  <div class="min-h-screen">
    <AppHeader />

    <!-- Hero -->
    <section class="relative overflow-hidden py-24 md:py-36">
      <!-- Background accent -->
      <div class="absolute inset-0 -z-10">
        <div class="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[500px]
                    bg-drape-gold/5 rounded-full blur-3xl" />
      </div>

      <div class="page-container text-center animate-fadeUp">
        <p class="text-drape-gold text-sm font-medium tracking-widest uppercase mb-6">
          AI-Powered Virtual Try-On
        </p>
        <h1 class="section-title text-5xl md:text-7xl mb-6 leading-tight">
          Try it on yourself.<br />
          <span class="text-drape-gold">Before you buy.</span>
        </h1>
        <p class="text-[var(--color-text-muted)] text-lg md:text-xl max-w-2xl mx-auto mb-10">
          Create your digital identity and instantly visualize how any product looks on
          you — dresses, blazers, shoes, watches. No more guessing.
        </p>
        <div class="flex flex-col sm:flex-row gap-4 justify-center">
          <RouterLink to="/login">
            <DrapeButton variant="gold" size="lg">Start for free</DrapeButton>
          </RouterLink>
          <RouterLink to="/catalog">
            <DrapeButton variant="ghost" size="lg">Browse catalog</DrapeButton>
          </RouterLink>
        </div>
      </div>
    </section>

    <!-- How it works -->
    <section class="py-24 border-t border-[var(--color-border)]">
      <div class="page-container">
        <h2 class="section-title text-center mb-16">How Drape works</h2>
        <div class="grid md:grid-cols-3 gap-8">
          <div
            v-for="(step, i) in steps"
            :key="i"
            class="card p-8 text-center"
          >
            <div class="w-12 h-12 rounded-full bg-drape-gold/10 text-drape-gold
                        flex items-center justify-center text-lg font-display font-bold mx-auto mb-6">
              {{ i + 1 }}
            </div>
            <h3 class="font-display text-xl font-semibold mb-3">{{ step.title }}</h3>
            <p class="text-[var(--color-text-muted)] text-sm leading-relaxed">{{ step.desc }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- CTA -->
    <section class="py-24 border-t border-[var(--color-border)]">
      <div class="page-container text-center">
        <h2 class="section-title mb-6">Ready to Drape?</h2>
        <p class="text-[var(--color-text-muted)] mb-8 text-lg">
          Join thousands of shoppers who buy with confidence.
        </p>
        <RouterLink to="/login">
          <DrapeButton variant="gold" size="lg">Create your identity</DrapeButton>
        </RouterLink>
      </div>
    </section>

    <!-- Footer -->
    <footer class="border-t border-[var(--color-border)] py-8">
      <div class="page-container flex flex-col md:flex-row items-center justify-between gap-4 text-sm text-[var(--color-text-muted)]">
        <span class="font-display font-semibold text-[var(--color-text)]">Drape</span>
        <p>© 2026 Drape. AI-powered virtual try-on.</p>
      </div>
    </footer>
  </div>
</template>

<script lang="ts">
const steps = [
  {
    title: 'Upload your photos',
    desc: 'Upload 4+ photos of yourself — front, side, and full body. Your data is private and secure.',
  },
  {
    title: 'Create your identity',
    desc: 'Our AI generates your personalized digital model in seconds, ready for try-on.',
  },
  {
    title: 'Try anything instantly',
    desc: 'Browse our catalog or paste any product URL. See how it looks on you in under 5 seconds.',
  },
]
</script>
