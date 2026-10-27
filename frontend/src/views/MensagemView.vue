<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import { api, exigir, type MensagemDetalhe } from '@/api/client'
import { BrButton, BrCard, BrMessage, BrTable } from '@/components/govbr'

const props = defineProps<{ id: string }>()
const mensagemId = computed(() => Number(props.id))

const mensagem = ref<MensagemDetalhe | null>(null)
const erro = ref('')
const reenviando = ref(false)
let atualizacao: ReturnType<typeof setInterval> | undefined

const STATUS = { PENDENTE: 'Na fila', ENVIADO: 'Enviado', ERRO: 'Erro' } as const

function quando(iso: string | null): string {
  return iso
    ? new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
    : ''
}

async function carregar() {
  try {
    const params = { path: { mensagem_id: mensagemId.value } }
    mensagem.value = await exigir(api.GET('/api/mensagens/{mensagem_id}', { params }))
    // Acompanha a fila enquanto houver e-mails pendentes
    if (!mensagem.value.pendentes) clearInterval(atualizacao)
  } catch (e) {
    erro.value = (e as Error).message
    clearInterval(atualizacao)
  }
}

async function reenviar() {
  reenviando.value = true
  try {
    const params = { path: { mensagem_id: mensagemId.value } }
    mensagem.value = await exigir(
      api.POST('/api/mensagens/{mensagem_id}/reenviar-falhas', { params }),
    )
    clearInterval(atualizacao)
    atualizacao = setInterval(carregar, 3000)
  } catch (e) {
    erro.value = (e as Error).message
  } finally {
    reenviando.value = false
  }
}

onMounted(async () => {
  await carregar()
  if (mensagem.value?.pendentes) atualizacao = setInterval(carregar, 3000)
})
onBeforeUnmount(() => clearInterval(atualizacao))
</script>

<template>
  <nav class="br-breadcrumb" aria-label="Breadcrumbs">
    <ol class="crumb-list">
      <li class="crumb"><RouterLink to="/mensagens">Mensagens</RouterLink></li>
      <li class="crumb" data-active="active">
        <i class="icon fas fa-chevron-right" aria-hidden="true"></i><span>Mensagem</span>
      </li>
    </ol>
  </nav>
  <BrMessage v-if="erro" estado="danger">{{ erro }}</BrMessage>

  <template v-if="mensagem">
    <h1 class="mb-1">{{ mensagem.assunto }}</h1>
    <p class="text-down-01">
      {{ quando(mensagem.criado_em) }}
      <template v-if="mensagem.disciplina">
        · {{ mensagem.disciplina }} – {{ mensagem.turma_nome }}
      </template>
    </p>

    <BrMessage v-if="mensagem.pendentes" estado="info">
      <i class="fas fa-spinner fa-spin" aria-hidden="true"></i>
      Enviando: {{ mensagem.enviados }} de {{ mensagem.total }}…
    </BrMessage>
    <BrMessage v-else-if="mensagem.erros" estado="danger" titulo="Alguns e-mails falharam.">
      {{ mensagem.erros }} não foram entregues ao servidor de e-mail.
    </BrMessage>
    <BrMessage v-else estado="success">
      Todos os {{ mensagem.total }} e-mails foram enviados.
    </BrMessage>

    <BrCard class="mb-3">
      <template #cabecalho><strong>Texto (modelo)</strong></template>
      <pre class="corpo">{{ mensagem.corpo }}</pre>
    </BrCard>

    <BrTable titulo="Destinatários">
      <template v-if="mensagem.erros" #acoes>
        <BrButton icone="fas fa-redo" :carregando="reenviando" @click="reenviar">
          Reenviar falhas
        </BrButton>
      </template>
      <thead>
        <tr>
          <th scope="col">Nome</th>
          <th scope="col">E-mail</th>
          <th scope="col">Situação</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="d in mensagem.destinatarios" :key="d.id">
          <td>
            {{ d.nome }}
            <span v-if="d.tipo === 'RESPONSAVEL'" class="text-down-01"> (responsável)</span>
          </td>
          <td>{{ d.email }}</td>
          <td>
            <span class="status" :class="d.status.toLowerCase()">{{ STATUS[d.status] }}</span>
            <span v-if="d.enviado_em" class="text-down-01"> · {{ quando(d.enviado_em) }}</span>
            <div v-if="d.erro" class="text-down-01 erro">
              {{ d.erro }} ({{ d.tentativas }} tentativa(s))
            </div>
          </td>
        </tr>
      </tbody>
    </BrTable>
  </template>
</template>

<style scoped>
.corpo {
  margin: 0;
  font-family: inherit;
  white-space: pre-wrap;
}

.status {
  font-weight: var(--font-weight-semi-bold);
}

.status.enviado {
  color: var(--success);
}

.status.erro,
.erro {
  color: var(--danger);
}

.status.pendente {
  color: var(--gray-60);
}
</style>
