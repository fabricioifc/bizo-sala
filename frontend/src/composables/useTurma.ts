import { ref, watchEffect, type Ref } from 'vue'

import { api, exigir, type Turma } from '@/api/client'

/** Carrega a turma da rota (usada no cabeçalho das telas da turma). */
export function useTurma(turmaId: Ref<number>) {
  const turma = ref<Turma | null>(null)
  const erro = ref('')

  async function recarregar() {
    try {
      const params = { path: { turma_id: turmaId.value } }
      turma.value = await exigir(api.GET('/api/turmas/{turma_id}', { params }))
    } catch (e) {
      erro.value = (e as Error).message
    }
  }

  watchEffect(recarregar)
  return { turma, erro, recarregar }
}
