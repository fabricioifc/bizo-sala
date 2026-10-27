import { defineStore } from 'pinia'
import { ref } from 'vue'

import { contarPendentes, sincronizarPendentes } from '@/offline/chamadas'

/** Chamadas guardadas no aparelho aguardando envio. */
export const useSincronizacaoStore = defineStore('sincronizacao', () => {
  const pendentes = ref(0)
  const erros = ref<string[]>([])
  const sincronizando = ref(false)

  async function atualizar() {
    pendentes.value = await contarPendentes()
  }

  async function sincronizar() {
    if (sincronizando.value || !navigator.onLine) return
    sincronizando.value = true
    try {
      const r = await sincronizarPendentes()
      erros.value.push(...r.erros)
    } finally {
      sincronizando.value = false
      await atualizar()
    }
  }

  return { pendentes, erros, sincronizando, atualizar, sincronizar }
})
