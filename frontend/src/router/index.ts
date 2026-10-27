import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'painel', component: () => import('@/views/PainelView.vue') },
    { path: '/turmas', name: 'turmas', component: () => import('@/views/TurmasView.vue') },
    { path: '/turmas/:id', redirect: (to) => `/turmas/${to.params.id}/aulas` },
    {
      path: '/turmas/:id/aulas',
      name: 'turma-aulas',
      component: () => import('@/views/TurmaAulasView.vue'),
      props: true,
    },
    {
      path: '/turmas/:id/estudantes',
      name: 'turma-estudantes',
      component: () => import('@/views/TurmaEstudantesView.vue'),
      props: true,
    },
    {
      path: '/turmas/:id/conteudo',
      name: 'turma-conteudo',
      component: () => import('@/views/TurmaConteudoView.vue'),
      props: true,
    },
    {
      path: '/aulas/:id/chamada',
      name: 'chamada',
      component: () => import('@/views/ChamadaView.vue'),
      props: true,
    },
    { path: '/cursos', name: 'cursos', component: () => import('@/views/CursosView.vue') },
    { path: '/periodos', name: 'periodos', component: () => import('@/views/PeriodosView.vue') },
    {
      path: '/dias-nao-letivos',
      name: 'dias-nao-letivos',
      component: () => import('@/views/DiasNaoLetivosView.vue'),
    },
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
