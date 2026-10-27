import { defineStore } from 'pinia'
import { ref } from 'vue'

import { api } from '@/api/client'

/** Quantidade de alertas ao SISAE pendentes (para o menu e o painel). */
export const useAlertasStore = defineStore('alertas', () => {
  const pendentes = ref(0)

  async function atualizar() {
    try {
      const { data } = await api.GET('/api/alertas/resumo')
      if (data) pendentes.value = data.pendentes
    } catch {
      // Sem conexão: mantém o último valor conhecido
    }
  }

  return { pendentes, atualizar }
})
