<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { useRouter } from 'vue-router'

import NavegacaoPrincipal from '@/components/NavegacaoPrincipal.vue'
import { BrButton, BrHeader, BrMessage } from '@/components/govbr'
import { useAuthStore } from '@/stores/auth'
import { useSincronizacaoStore } from '@/stores/sincronizacao'

const auth = useAuthStore()
const sincronizacao = useSincronizacaoStore()
const router = useRouter()

async function sair() {
  await auth.sair()
  await router.push({ name: 'entrar' })
}

// Envia chamadas guardadas no aparelho ao abrir o app e quando a conexão volta
const aoVoltarConexao = () => sincronizacao.sincronizar()
onMounted(async () => {
  window.addEventListener('online', aoVoltarConexao)
  await sincronizacao.atualizar()
  await sincronizacao.sincronizar()
})
onBeforeUnmount(() => window.removeEventListener('online', aoVoltarConexao))
</script>

<template>
  <BrHeader v-if="auth.usuario" titulo="Bizo Sala" logo="/logo.svg">
    <template #acoes>
      <BrButton
        v-if="sincronizacao.pendentes"
        densidade="small"
        icone="fas fa-cloud-upload-alt"
        :carregando="sincronizacao.sincronizando"
        :title="`${sincronizacao.pendentes} chamada(s) guardada(s) no aparelho`"
        @click="sincronizacao.sincronizar"
      >
        {{ sincronizacao.pendentes }} a enviar
      </BrButton>
      <span class="usuario d-none d-sm-inline">{{ auth.usuario.nome }}</span>
      <BrButton icone="fas fa-sign-out-alt" densidade="small" @click="sair">Sair</BrButton>
    </template>
  </BrHeader>
  <NavegacaoPrincipal v-if="auth.usuario" />
  <main class="container-lg py-3">
    <BrMessage
      v-for="(e, i) in sincronizacao.erros"
      :key="i"
      estado="danger"
      titulo="Chamada não enviada."
      fechavel
      @fechar="sincronizacao.erros.splice(i, 1)"
    >
      {{ e }}
    </BrMessage>
    <RouterView />
  </main>
</template>

<style scoped>
.usuario {
  margin-right: var(--spacing-scale-2x);
  color: var(--gray-60);
}
</style>
