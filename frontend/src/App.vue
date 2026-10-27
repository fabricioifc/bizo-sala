<script setup lang="ts">
import Button from 'primevue/button'
import Toast from 'primevue/toast'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function sair() {
  await auth.sair()
  await router.push({ name: 'entrar' })
}
</script>

<template>
  <Toast />
  <header v-if="auth.usuario" class="topo">
    <RouterLink to="/" class="marca">
      <img src="/logo.svg" alt="" width="28" height="28" />
      Bizo Sala
    </RouterLink>
    <Button label="Sair" icon="pi pi-sign-out" severity="secondary" text @click="sair" />
  </header>
  <main class="conteudo">
    <RouterView />
  </main>
</template>

<style scoped>
.topo {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1rem;
  background: var(--p-content-background);
  border-bottom: 1px solid var(--p-content-border-color);
}

.marca {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 600;
  color: inherit;
  text-decoration: none;
}
</style>
