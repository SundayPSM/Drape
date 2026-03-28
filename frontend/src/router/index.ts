import { createRouter, createWebHistory } from 'vue-router'
import { supabase } from '@/services/supabase'

const router = createRouter({
  history: createWebHistory(),
  scrollBehavior: () => ({ top: 0 }),
  routes: [
    {
      path: '/',
      name: 'landing',
      component: () => import('@/views/LandingView.vue'),
      meta: { public: true },
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/auth/LoginView.vue'),
      meta: { public: true, guestOnly: true },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('@/views/auth/RegisterView.vue'),
      meta: { public: true, guestOnly: true },
    },
    {
      // Supabase redirects here after Google OAuth
      path: '/auth/callback',
      name: 'auth-callback',
      component: () => import('@/views/auth/AuthCallbackView.vue'),
      meta: { public: true },
    },
    {
      path: '/onboarding',
      name: 'onboarding',
      component: () => import('@/views/OnboardingView.vue'),
    },
    {
      path: '/dashboard',
      name: 'dashboard',
      component: () => import('@/views/DashboardView.vue'),
    },
    {
      path: '/catalog',
      name: 'catalog',
      component: () => import('@/views/CatalogView.vue'),
    },
    {
      path: '/product/:id',
      name: 'product',
      component: () => import('@/views/ProductView.vue'),
    },
    {
      path: '/try-on',
      name: 'tryon',
      component: () => import('@/views/TryOnView.vue'),
    },
    {
      path: '/result/:jobId',
      name: 'result',
      component: () => import('@/views/ResultView.vue'),
    },
    {
      path: '/closet',
      name: 'closet',
      component: () => import('@/views/ClosetView.vue'),
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('@/views/SettingsView.vue'),
    },
  ],
})

// Auth guard — uses Supabase session
router.beforeEach(async (to) => {
  const { data } = await supabase.auth.getSession()
  const authenticated = !!data.session

  if (!to.meta.public && !authenticated) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (to.meta.guestOnly && authenticated) {
    return { name: 'dashboard' }
  }
})

export default router
