<script setup lang="ts">
import { useRouter } from 'vue-router'

import { BrButton, BrHeader } from '@/components/govbr'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function sair() {
  await auth.sair()
  await router.push({ name: 'entrar' })
}
</script>

<template>
  <BrHeader v-if="auth.usuario" titulo="Bizo Sala" logo="/logo.svg">
    <template #acoes>
      <span class="usuario d-none d-sm-inline">{{ auth.usuario.nome }}</span>
      <BrButton icone="fas fa-sign-out-alt" densidade="small" @click="sair">Sair</BrButton>
    </template>
  </BrHeader>
  <main class="container-lg py-3">
    <RouterView />
  </main>
</template>

<style scoped>
.usuario {
  margin-right: var(--spacing-scale-2x);
  color: var(--gray-60);
}
</style>
