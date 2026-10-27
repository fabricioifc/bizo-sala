import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'painel', component: () => import('@/views/PainelView.vue') },
    {
      path: '/entrar',
      name: 'entrar',
      component: () => import('@/views/LoginView.vue'),
      meta: { publica: true },
    },
  ],
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.carregado) await auth.carregar()

  if (!to.meta.publica && !auth.usuario) {
    return { name: 'entrar', query: to.fullPath !== '/' ? { voltar: to.fullPath } : {} }
  }
  if (to.name === 'entrar' && auth.usuario) return { name: 'painel' }
})

export default router
