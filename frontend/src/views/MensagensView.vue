<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api, exigir, type MensagemResumo } from '@/api/client'
import { BrMessage, BrTable } from '@/components/govbr'

const mensagens = ref<MensagemResumo[]>([])
const erro = ref('')

function quando(iso: string): string {
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

onMounted(async () => {
  try {
    mensagens.value = await exigir(api.GET('/api/mensagens'))
  } catch (e) {
    erro.value = (e as Error).message
  }
})
</script>

<template>
  <h1>Mensagens</h1>
  <p class="text-down-01">
    E-mails enviados pela sua conta institucional. Cada destinatário recebe um e-mail separado.
  </p>
  <BrMessage v-if="erro" estado="danger">{{ erro }}</BrMessage>

  <BrTable
    titulo="Mensagens enviadas"
    :vazia="mensagens.length === 0"
    mensagem-vazia="Nenhuma mensagem enviada ainda."
  >
    <template #acoes>
      <RouterLink to="/mensagens/nova" class="br-button primary">
        <i class="fas fa-paper-plane" aria-hidden="true"></i> Nova mensagem
      </RouterLink>
    </template>
    <thead>
      <tr>
        <th scope="col">Data</th>
        <th scope="col">Assunto</th>
        <th scope="col">Turma</th>
        <th scope="col">Envio</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="m in mensagens" :key="m.id">
        <td class="text-nowrap">{{ quando(m.criado_em) }}</td>
        <td>
          <RouterLink :to="`/mensagens/${m.id}`">{{ m.assunto }}</RouterLink>
        </td>
        <td>{{ m.disciplina ? `${m.disciplina} – ${m.turma_nome}` : '—' }}</td>
        <td class="text-nowrap">
          {{ m.enviados }}/{{ m.total }} enviados
          <span v-if="m.pendentes" class="text-down-01"> · {{ m.pendentes }} na fila</span>
          <span v-if="m.erros" class="erro"> · {{ m.erros }} com erro</span>
        </td>
      </tr>
    </tbody>
  </BrTable>
</template>

<style scoped>
.erro {
  color: var(--danger);
  font-weight: var(--font-weight-semi-bold);
}
</style>
