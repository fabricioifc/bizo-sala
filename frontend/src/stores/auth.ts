import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api, mensagemDeErro, type Usuario } from '@/api/client'

export const useAuthStore = defineStore('auth', () => {
  const usuario = ref<Usuario | null>(null)
  const carregado = ref(false)

  async function carregar() {
    const { data } = await api.GET('/api/auth/me')
    usuario.value = data ?? null
    carregado.value = true
  }

  async function entrar(email: string, senha: string) {
    const { data, error } = await api.POST('/api/auth/login', { body: { email, senha } })
    if (!data) throw new Error(mensagemDeErro(error, 'Não foi possível entrar'))
    usuario.value = data
  }

  async function sair() {
    await api.POST('/api/auth/logout')
    usuario.value = null
  }

  return { usuario, carregado, carregar, entrar, sair }
})
