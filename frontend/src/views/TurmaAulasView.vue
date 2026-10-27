<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { api, exigir, type Aula, type CargaHoraria, type FrequenciaEstudante } from '@/api/client'
import CabecalhoTurma from '@/components/CabecalhoTurma.vue'
import ModalConfirmacao from '@/components/ModalConfirmacao.vue'
import {
  BrButton,
  BrCard,
  BrCheckbox,
  BrInput,
  BrMessage,
  BrModal,
  BrSelect,
  BrTable,
  type Opcao,
} from '@/components/govbr'
import { useTurma } from '@/composables/useTurma'
import { formatarDataCurta, formatarNumero, hojeIso, nomeDoMes } from '@/utils/formato'

const props = defineProps<{ id: string }>()
const turmaId = computed(() => Number(props.id))
const { turma, erro: erroTurma } = useTurma(turmaId)

const aulas = ref<Aula[]>([])
const carga = ref<CargaHoraria | null>(null)
const frequencia = ref<FrequenciaEstudante[]>([])
const erro = ref('')
const aviso = ref('')
const gerando = ref(false)
const ocultarDadas = ref(false)

const hoje = hojeIso()

// Formulário de aula extra / edição
const formAula = ref<{ data: string; horas_aula: number | '' } | null>(null)
const editando = ref<Aula | null>(null)
const salvando = ref(false)
const erroForm = ref('')

// Cancelamento
const MOTIVOS = ['Recuperação paralela', 'Reavaliação', 'Evento institucional', 'Feriado/recesso']
const opcoesMotivo: Opcao<string>[] = [...MOTIVOS, 'Outro'].map((m) => ({ valor: m, rotulo: m }))
const cancelando = ref<Aula | null>(null)
const motivo = ref<string | null>(MOTIVOS[0]!)
const motivoOutro = ref('')
const erroCancelar = ref('')

const excluindo = ref<Aula | null>(null)

/** Aulas agrupadas por mês, na ordem do calendário */
const meses = computed(() => {
  const grupos = new Map<string, Aula[]>()
  for (const aula of aulas.value) {
    if (ocultarDadas.value && aula.status === 'DADA') continue
    const chave = aula.data.slice(0, 7)
    grupos.set(chave, [...(grupos.get(chave) ?? []), aula])
  }
  return [...grupos.entries()].map(([chave, lista]) => ({ nome: nomeDoMes(`${chave}-01`), lista }))
})

function situacao(aula: Aula): { rotulo: string; classe: string } {
  if (aula.status === 'DADA') return { rotulo: 'Chamada feita', classe: 'ok' }
  if (aula.status === 'CANCELADA') return { rotulo: 'Cancelada', classe: 'cancelada' }
  if (aula.data < hoje) return { rotulo: 'Em aberto', classe: 'aberta' }
  if (aula.data === hoje) return { rotulo: 'Hoje', classe: 'hoje' }
  return { rotulo: 'Prevista', classe: '' }
}

async function carregar() {
  try {
    const params = { path: { turma_id: turmaId.value } }
    ;[aulas.value, carga.value, frequencia.value] = await Promise.all([
      exigir(api.GET('/api/turmas/{turma_id}/aulas', { params })),
      exigir(api.GET('/api/turmas/{turma_id}/carga-horaria', { params })),
      exigir(api.GET('/api/turmas/{turma_id}/frequencia', { params })),
    ])
  } catch (e) {
    erro.value = (e as Error).message
  }
}

async function gerar() {
  gerando.value = true
  aviso.value = ''
  try {
    const params = { path: { turma_id: turmaId.value } }
    const { criadas } = await exigir(api.POST('/api/turmas/{turma_id}/aulas/gerar', { params }))
    aviso.value = criadas
      ? `${criadas} aula(s) criada(s) a partir dos horários da turma.`
      : 'O calendário já está completo; nenhuma aula nova foi criada.'
    await carregar()
  } catch (e) {
    erro.value = (e as Error).message
  } finally {
    gerando.value = false
  }
}

function novaExtra() {
  editando.value = null
  erroForm.value = ''
  formAula.value = { data: hoje, horas_aula: 1 }
}

function editar(aula: Aula) {
  editando.value = aula
  erroForm.value = ''
  formAula.value = { data: aula.data, horas_aula: aula.horas_aula }
}

async function salvarAula() {
  const f = formAula.value
  if (!f) return
  salvando.value = true
  erroForm.value = ''
  try {
    const body = { data: f.data, horas_aula: Number(f.horas_aula) }
    if (editando.value) {
      const params = { path: { aula_id: editando.value.id } }
      await exigir(api.PUT('/api/aulas/{aula_id}', { params, body }))
    } else {
      const params = { path: { turma_id: turmaId.value } }
      await exigir(api.POST('/api/turmas/{turma_id}/aulas', { params, body }))
    }
    formAula.value = null
    await carregar()
  } catch (e) {
    erroForm.value = (e as Error).message
  } finally {
    salvando.value = false
  }
}

function abrirCancelamento(aula: Aula) {
  cancelando.value = aula
  motivo.value = MOTIVOS[0]!
  motivoOutro.value = ''
  erroCancelar.value = ''
}

async function cancelar() {
  if (!cancelando.value) return
  const texto = motivo.value === 'Outro' ? motivoOutro.value.trim() : motivo.value
  if (!texto) throw new Error('Informe o motivo do cancelamento')
  const params = { path: { aula_id: cancelando.value.id } }
  await exigir(api.POST('/api/aulas/{aula_id}/cancelar', { params, body: { motivo: texto } }))
  await carregar()
}

async function reabrir(aula: Aula) {
  try {
    await exigir(
      api.POST('/api/aulas/{aula_id}/reabrir', { params: { path: { aula_id: aula.id } } }),
    )
    await carregar()
  } catch (e) {
    erro.value = (e as Error).message
  }
}

async function excluir() {
  if (!excluindo.value) return
  await exigir(
    api.DELETE('/api/aulas/{aula_id}', { params: { path: { aula_id: excluindo.value.id } } }),
  )
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <BrMessage v-if="erroTurma || erro" estado="danger">{{ erroTurma || erro }}</BrMessage>

  <template v-if="turma">
    <CabecalhoTurma :turma="turma" aba="aulas" />

    <!-- Carga horária -->
    <div v-if="carga" class="resumo">
      <BrCard>
        <div class="numero">
          {{ carga.dadas }}<small> / {{ carga.meta }}</small>
        </div>
        <div class="rotulo">horas-aula dadas / necessárias</div>
      </BrCard>
      <BrCard>
        <div class="numero">{{ carga.projecao }}</div>
        <div class="rotulo">projeção (dadas + previstas)</div>
      </BrCard>
      <BrCard :class="carga.saldo < 0 ? 'negativo' : 'positivo'">
        <div class="numero">{{ carga.saldo > 0 ? '+' : '' }}{{ carga.saldo }}</div>
        <div class="rotulo">
          {{ carga.saldo < 0 ? 'horas-aula faltando' : 'horas-aula de folga' }}
        </div>
      </BrCard>
      <BrCard>
        <div class="numero">{{ carga.canceladas }}</div>
        <div class="rotulo">horas-aula canceladas</div>
      </BrCard>
    </div>

    <BrMessage v-if="carga && carga.aulas_em_aberto" estado="warning" titulo="Chamadas pendentes.">
      {{ carga.aulas_em_aberto }} aula(s) passada(s) ainda sem chamada ({{ carga.em_aberto }}
      horas-aula).
    </BrMessage>
    <BrMessage v-if="carga && carga.saldo < 0 && aulas.length" estado="danger" titulo="Atenção.">
      Com as aulas previstas, faltarão {{ -carga.saldo }} horas-aula para cumprir a carga horária.
      Adicione aulas extras.
    </BrMessage>
    <BrMessage v-if="aviso" estado="success" fechavel @fechar="aviso = ''">{{ aviso }}</BrMessage>

    <!-- Calendário -->
    <BrTable
      titulo="Calendário de aulas"
      :vazia="aulas.length === 0"
      mensagem-vazia="Nenhuma aula ainda. Gere o calendário a partir dos horários da turma."
    >
      <template #acoes>
        <BrCheckbox v-model="ocultarDadas" rotulo="Ocultar aulas com chamada" />
        <BrButton icone="fas fa-magic" :carregando="gerando" @click="gerar">
          Gerar calendário
        </BrButton>
        <BrButton variante="primary" icone="fas fa-plus" @click="novaExtra">Aula extra</BrButton>
      </template>
      <thead>
        <tr>
          <th scope="col">Data</th>
          <th scope="col">Horas-aula</th>
          <th scope="col">Situação</th>
          <th scope="col"><span class="sr-only">Ações</span></th>
        </tr>
      </thead>
      <tbody v-for="mes in meses" :key="mes.nome">
        <tr class="mes">
          <th colspan="4" scope="rowgroup">{{ mes.nome }}</th>
        </tr>
        <tr
          v-for="aula in mes.lista"
          :key="aula.id"
          :class="{ cancelada: aula.status === 'CANCELADA', hoje: aula.data === hoje }"
        >
          <td class="text-nowrap">
            {{ formatarDataCurta(aula.data) }}
            <span v-if="aula.origem === 'EXTRA'" class="etiqueta">extra</span>
          </td>
          <td>{{ aula.horas_aula }}</td>
          <td>
            <span class="situacao" :class="situacao(aula).classe">{{ situacao(aula).rotulo }}</span>
            <div v-if="aula.motivo_cancelamento" class="text-down-01">
              {{ aula.motivo_cancelamento }}
            </div>
            <div v-if="aula.dia_nao_letivo" class="text-down-01 alerta">
              <i class="fas fa-exclamation-triangle" aria-hidden="true"></i>
              Dia não letivo: {{ aula.dia_nao_letivo }}
            </div>
          </td>
          <td class="text-right text-nowrap">
            <RouterLink
              v-if="aula.status !== 'CANCELADA'"
              :to="`/aulas/${aula.id}/chamada`"
              class="br-button small"
              :class="aula.status === 'DADA' ? 'secondary' : 'primary'"
            >
              <i class="fas fa-clipboard-check" aria-hidden="true"></i>
              {{ aula.status === 'DADA' ? 'Ver chamada' : 'Chamada' }}
            </RouterLink>
            <BrButton
              circular
              icone="fas fa-pen"
              :rotulo="`Editar aula de ${formatarDataCurta(aula.data)}`"
              @click="editar(aula)"
            />
            <BrButton
              v-if="aula.status === 'CANCELADA'"
              circular
              icone="fas fa-undo"
              :rotulo="`Reabrir aula de ${formatarDataCurta(aula.data)}`"
              @click="reabrir(aula)"
            />
            <BrButton
              v-else
              circular
              icone="fas fa-ban"
              :rotulo="`Cancelar aula de ${formatarDataCurta(aula.data)}`"
              @click="abrirCancelamento(aula)"
            />
            <BrButton
              circular
              icone="fas fa-trash"
              :rotulo="`Excluir aula de ${formatarDataCurta(aula.data)}`"
              @click="excluindo = aula"
            />
          </td>
        </tr>
      </tbody>
    </BrTable>

    <!-- Frequência -->
    <BrTable
      class="mt-4"
      titulo="Frequência dos estudantes"
      :vazia="frequencia.length === 0"
      mensagem-vazia="Nenhum estudante matriculado."
    >
      <thead>
        <tr>
          <th scope="col">Estudante</th>
          <th scope="col">Faltas (horas-aula)</th>
          <th scope="col">Presença</th>
          <th scope="col">Ainda pode faltar</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="f in frequencia"
          :key="f.estudante_id"
          :class="{ risco: f.faltas_restantes < 0 || (f.percentual_presenca ?? 100) < 75 }"
        >
          <td>
            {{ f.nome }}
            <span v-if="!f.ativo" class="etiqueta">inativo</span>
          </td>
          <td>{{ f.faltas }}</td>
          <td>
            {{ f.percentual_presenca === null ? '—' : `${formatarNumero(f.percentual_presenca)}%` }}
          </td>
          <td>{{ f.faltas_restantes >= 0 ? f.faltas_restantes : 'Reprovado por falta' }}</td>
        </tr>
      </tbody>
    </BrTable>
  </template>

  <BrModal
    v-if="formAula"
    :titulo="editando ? 'Editar aula' : 'Aula extra'"
    tamanho="small"
    @fechar="formAula = null"
  >
    <form id="form-aula" class="formulario" @submit.prevent="salvarAula">
      <BrInput v-model="formAula.data" rotulo="Data" type="date" required />
      <BrInput
        v-model="formAula.horas_aula"
        rotulo="Horas-aula (50 min)"
        type="number"
        min="1"
        max="8"
        required
      />
      <p v-if="!editando" class="text-down-01 mb-0">
        Pode ser em qualquer dia do período, inclusive num dia que já tem aula.
      </p>
      <BrMessage v-if="erroForm" estado="danger">{{ erroForm }}</BrMessage>
    </form>
    <template #rodape>
      <BrButton variante="secondary" @click="formAula = null">Cancelar</BrButton>
      <BrButton type="submit" form="form-aula" variante="primary" :carregando="salvando">
        Salvar
      </BrButton>
    </template>
  </BrModal>

  <ModalConfirmacao
    v-if="cancelando"
    titulo="Cancelar aula"
    rotulo-confirmar="Cancelar aula"
    :acao="cancelar"
    @fechar="cancelando = null"
  >
    <div class="formulario">
      <p class="mb-0">
        A aula de <strong>{{ formatarDataCurta(cancelando.data) }}</strong> deixa de contar na carga
        horária.
        <template v-if="cancelando.status === 'DADA'"
          >A chamada registrada será descartada.</template
        >
      </p>
      <BrSelect v-model="motivo" rotulo="Motivo" :opcoes="opcoesMotivo" />
      <BrInput v-if="motivo === 'Outro'" v-model="motivoOutro" rotulo="Descreva o motivo" />
    </div>
  </ModalConfirmacao>

  <ModalConfirmacao
    v-if="excluindo"
    titulo="Excluir aula"
    :acao="excluir"
    @fechar="excluindo = null"
  >
    Excluir a aula de <strong>{{ formatarDataCurta(excluindo.data) }}</strong
    >?
    <template v-if="excluindo.status === 'DADA'">
      A chamada registrada também será excluída.</template
    >
    <template v-if="excluindo.origem === 'GRADE'">
      Se quiser apenas que ela não conte carga horária, prefira cancelar. Ao gerar o calendário de
      novo, aulas da grade excluídas são recriadas.
    </template>
  </ModalConfirmacao>
</template>

<style scoped>
.resumo {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: var(--spacing-scale-2x);
  margin-bottom: var(--spacing-scale-2x);
}

.numero {
  font-size: var(--font-size-scale-up-04);
  font-weight: var(--font-weight-semi-bold);
}

.numero small {
  font-size: var(--font-size-scale-base);
  color: var(--gray-60);
}

.rotulo {
  color: var(--gray-60);
  font-size: var(--font-size-scale-down-01);
}

.negativo .numero {
  color: var(--danger);
}

.positivo .numero {
  color: var(--success);
}

tr.mes th {
  background: var(--gray-5);
  font-weight: var(--font-weight-semi-bold);
}

tr.cancelada td {
  color: var(--gray-50);
}

tr.hoje td {
  background: var(--blue-warm-vivid-10, var(--gray-5));
}

.situacao {
  font-weight: var(--font-weight-semi-bold);
}

.situacao.ok {
  color: var(--success);
}

.situacao.aberta {
  color: var(--warning-dark, var(--danger));
}

.situacao.hoje {
  color: var(--interactive);
}

.situacao.cancelada {
  color: var(--gray-60);
}

.alerta {
  color: var(--warning-dark, var(--danger));
}

.etiqueta {
  margin-left: var(--spacing-scale-half);
  padding: 0 var(--spacing-scale-half);
  border: 1px solid var(--border-color);
  border-radius: var(--surface-rounder-sm, 4px);
  font-size: var(--font-size-scale-down-02);
  color: var(--gray-60);
}

tr.risco td {
  color: var(--danger);
  font-weight: var(--font-weight-semi-bold);
}
</style>
