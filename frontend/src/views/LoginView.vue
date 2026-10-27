<script setup lang="ts">
import Button from 'primevue/button'
import Card from 'primevue/card'
import InputText from 'primevue/inputtext'
import Message from 'primevue/message'
import Password from 'primevue/password'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

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
    <Card>
      <template #title>
        <div class="titulo">
          <img src="/logo.svg" alt="" width="40" height="40" />
          Bizo Sala
        </div>
      </template>
      <template #content>
        <form class="formulario" @submit.prevent="entrar">
          <label for="email">E-mail</label>
          <InputText id="email" v-model="email" type="email" autocomplete="username" required />

          <label for="senha">Senha</label>
          <Password
            v-model="senha"
            input-id="senha"
            :feedback="false"
            toggle-mask
            fluid
            autocomplete="current-password"
            required
          />

          <Message v-if="erro" severity="error" :closable="false">{{ erro }}</Message>

          <Button type="submit" label="Entrar" :loading="enviando" />
        </form>
      </template>
    </Card>
  </div>
</template>

<style scoped>
.login {
  max-width: 380px;
  margin: 10vh auto 0;
}

.titulo {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.formulario {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.formulario button {
  margin-top: 0.75rem;
}
</style>
