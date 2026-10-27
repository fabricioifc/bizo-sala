<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { BrButton, BrCard, BrInput, BrMessage } from '@/components/govbr'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const senha = ref('')
const erro = ref('')
const enviando = ref(false)

async function entrar() {
  erro.value = ''
  enviando.value = true
  try {
    await auth.entrar(email.value, senha.value)
    const voltar = typeof route.query.voltar === 'string' ? route.query.voltar : '/'
    await router.push(voltar)
  } catch (e) {
    erro.value = e instanceof Error ? e.message : 'Não foi possível entrar'
  } finally {
    enviando.value = false
  }
}
</script>

<template>
  <div class="login">
    <BrCard>
      <template #cabecalho>
        <div class="titulo">
          <img src="/logo.svg" alt="" width="40" height="40" />
          <h1>Bizo Sala</h1>
        </div>
      </template>

      <form class="formulario" @submit.prevent="entrar">
        <BrInput
          v-model="email"
          rotulo="E-mail"
          type="email"
          placeholder="seu.nome@ifc.edu.br"
          autocomplete="username"
          required
        />
        <BrInput
          v-model="senha"
          rotulo="Senha"
          type="password"
          autocomplete="current-password"
          required
        />

        <BrMessage v-if="erro" estado="danger">{{ erro }}</BrMessage>

        <BrButton type="submit" variante="primary" bloco :carregando="enviando">Entrar</BrButton>
      </form>
    </BrCard>
  </div>
</template>

<style scoped>
.login {
  max-width: 400px;
  margin: 10vh auto 0;
}

.titulo {
  display: flex;
  align-items: center;
  gap: var(--spacing-scale-2x);
}

.titulo h1 {
  margin: 0;
  font-size: var(--font-size-scale-up-02);
}

.formulario {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-scale-2x);
}
</style>
