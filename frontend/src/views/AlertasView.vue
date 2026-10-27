<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'

import { api, exigir, type Alerta } from '@/api/client'
import { BrButton, BrCard, BrMessage, BrModal, BrTextarea } from '@/components/govbr'
import { useAlertasStore } from '@/stores/alertas'
import { descreverAlerta, textoParaSisae } from '@/utils/alertas'
import { formatarData } from '@/utils/formato'

type Aba = 'PENDENTE' | 'RESOLVIDOS'

const loja = useAlertasStore()
const aba = ref<Aba>('PENDENTE')
const alertas = ref<Alerta[]>([])
const carregando = ref(false)
const erro = ref('')
const copiado = ref<number | null>(null)

const resolvendo = ref<{ alerta: Alerta; status: 'AVISADO' | 'DESCARTADO' } | null>(null)
const observacao = ref('')
const salvando = ref(false)
const erroModal = ref('')

async function carregar() {
  carregando.value = true
  erro.value = ''
  try {
    const todos = await exigir(
      api.GET('/api/alertas', {
        params: { query: aba.value === 'PENDENTE' ? { status: 'PENDENTE' } : {} },
      }),
    )
    alertas.value = aba.value === 'PENDENTE' ? todos : todos.filter((a) => a.status !== 'PENDENTE')
  } catch (e) {
    erro.value = (e as Error).message
  } finally {
    carregando.value = false
  }
  await loja.atualizar()
}

async function copiar(alerta: Alerta) {
  try {
    await navigator.clipboard.writeText(textoParaSisae(alerta))
    copiado.value = alerta.id
    setTimeout(() => (copiado.value = null), 2500)
  } catch {
    erro.value = 'Não foi possível copiar. Selecione o texto manualmente.'
  }
}

function abrir(alerta: Alerta, status: 'AVISADO' | 'DESCARTADO') {
  resolvendo.value = { alerta, status }
  observacao.value = ''
  erroModal.value = ''
}

async function enviarResolucao(status: Alerta['status'], alerta: Alerta, obs: string | null) {
  const params = { path: { alerta_id: alerta.id } }
  await exigir(
    api.POST('/api/alertas/{alerta_id}/resolver', { params, body: { status, observacao: obs } }),
  )
}

async function confirmar() {
  if (!resolvendo.value) return
  salvando.value = true
  try {
    const { alerta, status } = resolvendo.value
    await enviarResolucao(status, alerta, observacao.value.trim() || null)
    resolvendo.value = null
    await carregar()
  } catch (e) {
    erroModal.value = (e as Error).message
  } finally {
    salvando.value = false
  }
}

async function reabrir(alerta: Alerta) {
  try {
    await enviarResolucao('PENDENTE', alerta, null)
    await carregar()
  } catch (e) {
    erro.value = (e as Error).message
  }
}

watch(aba, carregar)
onMounted(carregar)
</script>

<template>
  <h1>Alertas ao SISAE</h1>
  <p class="text-down-01">
    Estudantes do ensino médio integrado que faltaram o dia inteiro em encontros seguidos ou que
    acumularam faltas, conforme os limites configurados em cada curso. Atrasos não contam.
  </p>

  <div class="br-tab mb-3">
    <nav class="tab-nav" aria-label="Situação dos alertas">
      <ul>
        <li class="tab-item" :class="{ active: aba === 'PENDENTE' }">
          <button type="button" :aria-pressed="aba === 'PENDENTE'" @click="aba = 'PENDENTE'">
            <span class="name">Pendentes ({{ loja.pendentes }})</span>
          </button>
        </li>
        <li class="tab-item" :class="{ active: aba === 'RESOLVIDOS' }">
          <button type="button" :aria-pressed="aba === 'RESOLVIDOS'" @click="aba = 'RESOLVIDOS'">
            <span class="name">Resolvidos</span>
          </button>
        </li>
      </ul>
    </nav>
  </div>

  <BrMessage v-if="erro" estado="danger">{{ erro }}</BrMessage>
  <BrMessage v-if="!carregando && alertas.length === 0" estado="success">
    {{ aba === 'PENDENTE' ? 'Nenhum alerta pendente.' : 'Nenhum alerta resolvido ainda.' }}
  </BrMessage>

  <div class="alertas">
    <BrCard v-for="alerta in alertas" :key="alerta.id">
      <template #cabecalho>
        <div class="cabecalho">
          <strong>{{ alerta.estudante_nome }}</strong>
          <span class="tipo" :class="alerta.tipo.toLowerCase()">{{ descreverAlerta(alerta) }}</span>
        </div>
      </template>
      <dl>
        <dt>Turma</dt>
        <dd>
          <RouterLink :to="`/turmas/${alerta.turma_id}/aulas`">
            {{ alerta.disciplina }} – {{ alerta.turma_nome }}
          </RouterLink>
        </dd>
        <dt>Matrícula</dt>
        <dd>{{ alerta.matricula }}</dd>
        <dt>Faltas nos dias</dt>
        <dd>{{ alerta.datas.map(formatarData).join(', ') }}</dd>
        <template v-if="alerta.email_responsavel">
          <dt>Responsável</dt>
          <dd>{{ alerta.email_responsavel }}</dd>
        </template>
        <template v-if="alerta.status !== 'PENDENTE'">
          <dt>Situação</dt>
          <dd>
            {{ alerta.status === 'AVISADO' ? 'SISAE avisado' : 'Descartado' }}
            <template v-if="alerta.resolvido_em">
              em {{ formatarData(alerta.resolvido_em.slice(0, 10)) }}
            </template>
            <div v-if="alerta.observacao" class="text-down-01">{{ alerta.observacao }}</div>
          </dd>
        </template>
      </dl>
      <template #rodape>
        <div class="acoes">
          <BrButton
            densidade="small"
            :icone="copiado === alerta.id ? 'fas fa-check' : 'fas fa-copy'"
            @click="copiar(alerta)"
          >
            {{ copiado === alerta.id ? 'Copiado' : 'Copiar texto' }}
          </BrButton>
          <template v-if="alerta.status === 'PENDENTE'">
            <BrButton densidade="small" icone="fas fa-times" @click="abrir(alerta, 'DESCARTADO')">
              Descartar
            </BrButton>
            <BrButton
              densidade="small"
              variante="primary"
              icone="fas fa-check"
              @click="abrir(alerta, 'AVISADO')"
            >
              SISAE avisado
            </BrButton>
          </template>
          <BrButton v-else densidade="small" icone="fas fa-undo" @click="reabrir(alerta)">
            Reabrir
          </BrButton>
        </div>
      </template>
    </BrCard>
  </div>

  <BrModal
    v-if="resolvendo"
    :titulo="resolvendo.status === 'AVISADO' ? 'Marcar como avisado' : 'Descartar alerta'"
    tamanho="small"
    @fechar="resolvendo = null"
  >
    <div class="formulario">
      <p class="mb-0">
        <strong>{{ resolvendo.alerta.estudante_nome }}</strong> –
        {{ descreverAlerta(resolvendo.alerta) }}
      </p>
      <BrTextarea
        v-model="observacao"
        :rotulo="resolvendo.status === 'AVISADO' ? 'Observação (opcional)' : 'Motivo (opcional)'"
        :placeholder="
          resolvendo.status === 'AVISADO'
            ? 'Ex.: avisado por e-mail à coordenação do SISAE'
            : 'Ex.: faltas justificadas com atestado'
        "
        :maxlength="500"
        :linhas="3"
      />
      <BrMessage v-if="erroModal" estado="danger">{{ erroModal }}</BrMessage>
    </div>
    <template #rodape>
      <BrButton variante="secondary" @click="resolvendo = null">Cancelar</BrButton>
      <BrButton variante="primary" :carregando="salvando" @click="confirmar">Confirmar</BrButton>
    </template>
  </BrModal>
</template>

<style scoped>
.alertas {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-scale-2x);
}

.cabecalho {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-scale-base);
}

.tipo {
  padding: 0 var(--spacing-scale-base);
  border-radius: var(--surface-rounder-sm, 4px);
  font-size: var(--font-size-scale-down-01);
  font-weight: var(--font-weight-semi-bold);
  color: var(--pure-0, #fff);
  background: var(--danger);
}

.tipo.alternadas {
  background: var(--warning-dark, #b38c00);
}

dl {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: var(--spacing-scale-half) var(--spacing-scale-2x);
  margin: 0;
}

dt {
  color: var(--gray-60);
}

dd {
  margin: 0;
}

.acoes {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--spacing-scale-base);
}
</style>
