<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import {
  api,
  exigir,
  type Avaliacao,
  type AvaliacaoEntrada,
  type Boletim,
  type NotaEntrada,
  type NotaLancada,
} from '@/api/client'
import CabecalhoTurma from '@/components/CabecalhoTurma.vue'
import ModalConfirmacao from '@/components/ModalConfirmacao.vue'
import {
  BrButton,
  BrInput,
  BrMessage,
  BrModal,
  BrSelect,
  BrTable,
  type Opcao,
} from '@/components/govbr'
import { useTurma } from '@/composables/useTurma'
import { formatarData, formatarNumero } from '@/utils/formato'
import { formatarNota, lerNota, SITUACOES, SUBSTITUICOES } from '@/utils/notas'

type Substituicao = NonNullable<Avaliacao['substituicao']>

const props = defineProps<{ id: string }>()
const turmaId = computed(() => Number(props.id))
const { turma, erro: erroTurma } = useTurma(turmaId)

const avaliacoes = ref<Avaliacao[]>([])
const boletim = ref<Boletim | null>(null)
const erro = ref('')
/** 'final' = aba de resultado final; número = id do ciclo */
const aba = ref<number | 'final'>('final')

// Planilha: textos digitados e escolhas de substituição, por "avaliacao:estudante"
const textos = ref<Record<string, string>>({})
const escolhas = ref<Record<string, number | null>>({})
const originais = ref<Record<string, { texto: string; escolha: number | null }>>({})
const salvando = ref(false)
const salvo = ref(false)

// Formulário de avaliação
const formAvaliacao = ref<AvaliacaoEntrada | null>(null)
const editandoAvaliacao = ref<Avaliacao | null>(null)
const salvandoAvaliacao = ref(false)
const erroAvaliacao = ref('')
const excluindo = ref<Avaliacao | null>(null)

const chave = (avaliacaoId: number, estudanteId: number) => `${avaliacaoId}:${estudanteId}`
const ehEmi = computed(() => turma.value?.nivel === 'EMI')
const ciclos = computed(() => boletim.value?.ciclos ?? [])
const cicloAtual = computed(() => ciclos.value.find((c) => c.ciclo_id === aba.value) ?? null)
const doCiclo = computed(() => avaliacoes.value.filter((a) => a.ciclo_id === aba.value))
const regularesDoCiclo = computed(() => doCiclo.value.filter((a) => a.tipo === 'REGULAR'))
const estudantes = computed(() => boletim.value?.estudantes ?? [])

const alteradas = computed(() =>
  Object.keys(textos.value).filter(
    (k) =>
      textos.value[k] !== originais.value[k]?.texto ||
      (escolhas.value[k] ?? null) !== (originais.value[k]?.escolha ?? null),
  ),
)
const invalidas = computed(
  () => new Set(Object.keys(textos.value).filter((k) => lerNota(textos.value[k]!) === 'invalida')),
)

function resultadoDoCiclo(estudanteId: number, cicloId: number) {
  return estudantes.value
    .find((e) => e.estudante_id === estudanteId)
    ?.ciclos.find((c) => c.ciclo_id === cicloId)
}

/** Avaliação substituída pela recuperação deste estudante (para mostrar na planilha) */
function substituidaPor(avaliacaoId: number, estudanteId: number): boolean {
  return !!resultadoDoCiclo(estudanteId, aba.value as number)?.substituicoes.some(
    (s) => s.avaliacao_id === avaliacaoId,
  )
}

const abaixoDaMedia = computed(() =>
  estudantes.value.filter(
    (e) => resultadoDoCiclo(e.estudante_id, aba.value as number)?.abaixo_da_media,
  ),
)

function opcoesSubstituicao(): Opcao<Substituicao>[] {
  return (Object.keys(SUBSTITUICOES) as Substituicao[]).map((valor) => ({
    valor,
    rotulo: SUBSTITUICOES[valor],
  }))
}

const opcoesTipo: Opcao<'REGULAR' | 'RECUPERACAO'>[] = [
  { valor: 'REGULAR', rotulo: 'Avaliação regular' },
  { valor: 'RECUPERACAO', rotulo: 'Recuperação / reavaliação' },
]

function preencherPlanilha(notas: NotaLancada[]) {
  const t: Record<string, string> = {}
  const e: Record<string, number | null> = {}
  for (const est of estudantes.value) {
    for (const av of avaliacoes.value) {
      t[chave(av.id, est.estudante_id)] = ''
      e[chave(av.id, est.estudante_id)] = null
    }
  }
  for (const n of notas) {
    t[chave(n.avaliacao_id, n.estudante_id)] = formatarNota(n.valor)
    e[chave(n.avaliacao_id, n.estudante_id)] = n.substitui_avaliacao_id
  }
  textos.value = t
  escolhas.value = e
  originais.value = Object.fromEntries(
    Object.keys(t).map((k) => [k, { texto: t[k]!, escolha: e[k] ?? null }]),
  )
}

async function carregar() {
  try {
    const params = { path: { turma_id: turmaId.value } }
    const [avs, notas, bol] = await Promise.all([
      exigir(api.GET('/api/turmas/{turma_id}/avaliacoes', { params })),
      exigir(api.GET('/api/turmas/{turma_id}/notas', { params })),
      exigir(api.GET('/api/turmas/{turma_id}/boletim', { params })),
    ])
    avaliacoes.value = avs
    boletim.value = bol
    preencherPlanilha(notas)
    if (aba.value === 'final' && bol.ciclos.length && !salvo.value) {
      aba.value = cicloEmAndamento(bol) ?? 'final'
    }
  } catch (e) {
    erro.value = (e as Error).message
  }
}

/** Abre no ciclo de hoje (ou no último que já começou) */
function cicloEmAndamento(bol: Boletim): number | null {
  const hoje = new Date().toISOString().slice(0, 10)
  const iniciados = bol.ciclos.filter((c) => c.data_inicio <= hoje)
  return (iniciados[iniciados.length - 1] ?? bol.ciclos[0])?.ciclo_id ?? null
}

async function salvarNotas() {
  if (invalidas.value.size) {
    erro.value = 'Corrija as notas em vermelho: use valores de 0 a 10 com até uma casa decimal.'
    return
  }
  salvando.value = true
  erro.value = ''
  try {
    const body: NotaEntrada[] = alteradas.value.map((k) => {
      const [avaliacao_id, estudante_id] = k.split(':').map(Number) as [number, number]
      const valor = lerNota(textos.value[k]!) as number | null
      return {
        avaliacao_id,
        estudante_id,
        valor,
        substitui_avaliacao_id: escolhas.value[k] ?? null,
      }
    })
    await exigir(
      api.PUT('/api/turmas/{turma_id}/notas', {
        params: { path: { turma_id: turmaId.value } },
        body,
      }),
    )
    salvo.value = true
    await carregar()
  } catch (e) {
    erro.value = (e as Error).message
  } finally {
    salvando.value = false
  }
}

// --- Avaliações ---------------------------------------------------------------

function novaAvaliacao() {
  editandoAvaliacao.value = null
  erroAvaliacao.value = ''
  formAvaliacao.value = {
    ciclo_id: aba.value as number,
    nome: '',
    data: null,
    peso: 1,
    tipo: 'REGULAR',
    substituicao: null,
    substitui_avaliacao_id: null,
  }
}

function editarAvaliacao(av: Avaliacao) {
  editandoAvaliacao.value = av
  erroAvaliacao.value = ''
  formAvaliacao.value = {
    ciclo_id: av.ciclo_id,
    nome: av.nome,
    data: av.data,
    peso: av.peso,
    tipo: av.tipo,
    substituicao: av.substituicao,
    substitui_avaliacao_id: av.substitui_avaliacao_id,
  }
}

function trocarTipo(tipo: 'REGULAR' | 'RECUPERACAO' | null) {
  const f = formAvaliacao.value
  if (!f || !tipo) return
  f.tipo = tipo
  if (tipo === 'RECUPERACAO') {
    f.substituicao = f.substituicao ?? (ehEmi.value ? 'CICLO' : 'MELHOR')
    if (!f.nome) f.nome = ehEmi.value ? 'Recuperação' : 'Reavaliação'
  } else {
    f.substituicao = null
    f.substitui_avaliacao_id = null
  }
}

async function salvarAvaliacao() {
  const f = formAvaliacao.value
  if (!f) return
  salvandoAvaliacao.value = true
  erroAvaliacao.value = ''
  try {
    const body = { ...f, peso: Number(f.peso), data: f.data || null }
    if (editandoAvaliacao.value) {
      const params = { path: { avaliacao_id: editandoAvaliacao.value.id } }
      await exigir(api.PUT('/api/avaliacoes/{avaliacao_id}', { params, body }))
    } else {
      const params = { path: { turma_id: turmaId.value } }
      await exigir(api.POST('/api/turmas/{turma_id}/avaliacoes', { params, body }))
    }
    formAvaliacao.value = null
    await carregar()
  } catch (e) {
    erroAvaliacao.value = (e as Error).message
  } finally {
    salvandoAvaliacao.value = false
  }
}

async function excluirAvaliacao() {
  if (!excluindo.value) return
  const params = { path: { avaliacao_id: excluindo.value.id } }
  await exigir(api.DELETE('/api/avaliacoes/{avaliacao_id}', { params }))
  await carregar()
}

// --- Saída com alterações -------------------------------------------------

function avisarAoSair(evento: BeforeUnloadEvent) {
  if (alteradas.value.length) evento.preventDefault()
}

onBeforeRouteLeave(() =>
  alteradas.value.length ? window.confirm('Há notas não salvas. Sair mesmo assim?') : true,
)
onMounted(() => {
  carregar()
  window.addEventListener('beforeunload', avisarAoSair)
})
onBeforeUnmount(() => window.removeEventListener('beforeunload', avisarAoSair))
</script>

<template>
  <BrMessage v-if="erroTurma" estado="danger">{{ erroTurma }}</BrMessage>

  <template v-if="turma && boletim">
    <CabecalhoTurma :turma="turma" aba="notas" />

    <!-- Ciclos -->
    <div class="br-tab small mb-3">
      <nav class="tab-nav" aria-label="Ciclos avaliativos">
        <ul>
          <li
            v-for="c in ciclos"
            :key="c.ciclo_id"
            class="tab-item"
            :class="{ active: aba === c.ciclo_id }"
          >
            <button type="button" :aria-pressed="aba === c.ciclo_id" @click="aba = c.ciclo_id">
              <span class="name">{{ c.nome }}</span>
            </button>
          </li>
          <li class="tab-item" :class="{ active: aba === 'final' }">
            <button type="button" :aria-pressed="aba === 'final'" @click="aba = 'final'">
              <span class="name">Resultado final</span>
            </button>
          </li>
        </ul>
      </nav>
    </div>

    <BrMessage v-if="erro" estado="danger" fechavel @fechar="erro = ''">{{ erro }}</BrMessage>

    <!-- Planilha do ciclo -->
    <template v-if="cicloAtual">
      <p class="text-down-01">
        {{ formatarData(cicloAtual.data_inicio) }} a {{ formatarData(cicloAtual.data_fim) }} · nota
        do ciclo = média ponderada das avaliações regulares · média para aprovação
        {{ formatarNumero(boletim.media_aprovacao) }}
      </p>

      <BrTable
        :titulo="`Notas – ${cicloAtual.nome}`"
        :vazia="doCiclo.length === 0 || estudantes.length === 0"
        :mensagem-vazia="
          estudantes.length === 0
            ? 'Nenhum estudante matriculado.'
            : 'Nenhuma avaliação neste ciclo. Crie a primeira.'
        "
      >
        <template #acoes>
          <BrButton variante="primary" icone="fas fa-plus" @click="novaAvaliacao">
            Nova avaliação
          </BrButton>
        </template>
        <thead v-if="doCiclo.length && estudantes.length">
          <tr>
            <th scope="col">Estudante</th>
            <th
              v-for="av in doCiclo"
              :key="av.id"
              scope="col"
              class="coluna-nota"
              :class="{ recuperacao: av.tipo === 'RECUPERACAO' }"
            >
              <div class="titulo-avaliacao">
                <span>{{ av.nome }}</span>
                <span class="acoes-avaliacao">
                  <BrButton
                    circular
                    densidade="small"
                    icone="fas fa-pen"
                    :rotulo="`Editar ${av.nome}`"
                    @click="editarAvaliacao(av)"
                  />
                  <BrButton
                    circular
                    densidade="small"
                    icone="fas fa-trash"
                    :rotulo="`Excluir ${av.nome}`"
                    @click="excluindo = av"
                  />
                </span>
              </div>
              <div class="text-down-02 detalhe">
                <template v-if="av.tipo === 'REGULAR'">peso {{ formatarNumero(av.peso) }}</template>
                <template v-else
                  >substitui: {{ SUBSTITUICOES[av.substituicao!].toLowerCase() }}</template
                >
                <template v-if="av.data"> · {{ formatarData(av.data) }}</template>
              </div>
            </th>
            <th scope="col" class="coluna-nota">Nota do ciclo</th>
          </tr>
        </thead>
        <tbody v-if="doCiclo.length">
          <tr v-for="est in estudantes" :key="est.estudante_id" :class="{ inativo: !est.ativo }">
            <th scope="row" class="nome">{{ est.nome }}</th>
            <td
              v-for="av in doCiclo"
              :key="av.id"
              class="coluna-nota"
              :class="{ recuperacao: av.tipo === 'RECUPERACAO' }"
            >
              <div
                class="br-input small celula"
                :class="{
                  danger: invalidas.has(chave(av.id, est.estudante_id)),
                  substituida: substituidaPor(av.id, est.estudante_id),
                }"
              >
                <input
                  v-model="textos[chave(av.id, est.estudante_id)]"
                  type="text"
                  inputmode="decimal"
                  maxlength="4"
                  :aria-label="`${av.nome} de ${est.nome}`"
                  :aria-invalid="invalidas.has(chave(av.id, est.estudante_id)) || undefined"
                  :title="
                    substituidaPor(av.id, est.estudante_id)
                      ? 'Substituída pela recuperação'
                      : undefined
                  "
                />
              </div>
              <select
                v-if="
                  av.tipo === 'RECUPERACAO' &&
                  av.substituicao !== 'CICLO' &&
                  textos[chave(av.id, est.estudante_id)]
                "
                v-model="escolhas[chave(av.id, est.estudante_id)]"
                class="escolha"
                :aria-label="`Avaliação que a ${av.nome} de ${est.nome} substitui`"
              >
                <option :value="null">
                  {{ av.substituicao === 'MELHOR' ? 'Automático (melhor)' : 'Padrão da avaliação' }}
                </option>
                <option v-for="r in regularesDoCiclo" :key="r.id" :value="r.id">
                  {{ r.nome }}
                </option>
              </select>
            </td>
            <td class="coluna-nota media">
              <template
                v-if="resultadoDoCiclo(est.estudante_id, cicloAtual.ciclo_id)?.media !== null"
              >
                <strong
                  :class="{
                    abaixo: resultadoDoCiclo(est.estudante_id, cicloAtual.ciclo_id)
                      ?.abaixo_da_media,
                  }"
                >
                  {{ formatarNota(resultadoDoCiclo(est.estudante_id, cicloAtual.ciclo_id)?.media) }}
                </strong>
                <div
                  v-if="
                    resultadoDoCiclo(est.estudante_id, cicloAtual.ciclo_id)?.substituicoes.length
                  "
                  class="text-down-02 detalhe"
                >
                  antes da rec.:
                  {{
                    formatarNota(
                      resultadoDoCiclo(est.estudante_id, cicloAtual.ciclo_id)
                        ?.media_sem_recuperacao,
                    )
                  }}
                </div>
              </template>
              <template v-else>—</template>
            </td>
          </tr>
        </tbody>
      </BrTable>

      <!-- Recuperação paralela -->
      <BrMessage
        v-if="abaixoDaMedia.length"
        class="mt-3"
        estado="warning"
        :titulo="ehEmi ? 'Recuperação paralela:' : 'Abaixo da média:'"
      >
        {{ abaixoDaMedia.map((e) => e.nome).join(', ') }}.
        <template v-if="ehEmi">
          Estudantes abaixo de {{ formatarNumero(boletim.media_aprovacao) }} devem ser convocados
          (responsáveis informados) e só fazem a reavaliação se participarem de ao menos 75% dos
          encontros de recuperação (OD arts. 243 e 246).
        </template>
      </BrMessage>
      <p v-if="ehEmi && cicloAtual.horas_aula_dadas" class="text-down-01 mt-2">
        Carga horária de recuperação paralela neste trimestre: de
        {{ cicloAtual.recuperacao_min }} a {{ cicloAtual.recuperacao_max }} horas-aula (10% a 20%
        das {{ cicloAtual.horas_aula_dadas }} horas-aula dadas, OD art. 242). Se usar uma aula para
        a recuperação, cancele-a com o motivo "Recuperação paralela".
      </p>

      <div v-if="doCiclo.length && estudantes.length" class="rodape">
        <div class="conteudo-rodape">
          <span v-if="invalidas.size" class="text-danger"
            >{{ invalidas.size }} nota(s) inválida(s)</span
          >
          <span v-else-if="alteradas.length" class="text-down-01">
            {{ alteradas.length }} alteração(ões) não salva(s)
          </span>
          <span v-else-if="salvo" class="text-down-01">
            <i class="fas fa-check" aria-hidden="true"></i> Notas salvas
          </span>
          <BrButton
            variante="primary"
            icone="fas fa-save"
            :carregando="salvando"
            :disabled="!alteradas.length"
            @click="salvarNotas"
          >
            Salvar notas
          </BrButton>
        </div>
      </div>
    </template>

    <!-- Resultado final -->
    <BrTable
      v-else
      titulo="Resultado final"
      :vazia="estudantes.length === 0"
      mensagem-vazia="Nenhum estudante matriculado."
    >
      <thead>
        <tr>
          <th scope="col">Estudante</th>
          <th v-for="c in ciclos" :key="c.ciclo_id" scope="col" class="coluna-nota">
            {{ c.nome }}
          </th>
          <th scope="col" class="coluna-nota">Média final</th>
          <th scope="col">Presença</th>
          <th scope="col">Situação</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="est in estudantes" :key="est.estudante_id" :class="{ inativo: !est.ativo }">
          <th scope="row" class="nome">{{ est.nome }}</th>
          <td v-for="c in est.ciclos" :key="c.ciclo_id" class="coluna-nota">
            <span :class="{ abaixo: c.abaixo_da_media }">{{ formatarNota(c.media) || '—' }}</span>
          </td>
          <td class="coluna-nota media">
            <strong
              :class="{
                abaixo: est.media_final !== null && est.media_final < boletim.media_aprovacao,
              }"
            >
              {{ formatarNota(est.media_final) || '—' }}
            </strong>
          </td>
          <td>
            {{
              est.percentual_presenca === null ? '—' : `${formatarNumero(est.percentual_presenca)}%`
            }}
          </td>
          <td>
            <span class="situacao" :class="est.situacao.toLowerCase()">
              {{ SITUACOES[est.situacao] }}
            </span>
          </td>
        </tr>
      </tbody>
    </BrTable>
  </template>

  <BrModal
    v-if="formAvaliacao"
    :titulo="editandoAvaliacao ? 'Editar avaliação' : 'Nova avaliação'"
    @fechar="formAvaliacao = null"
  >
    <form id="form-avaliacao" class="formulario" @submit.prevent="salvarAvaliacao">
      <BrSelect
        :model-value="formAvaliacao.tipo ?? 'REGULAR'"
        rotulo="Tipo"
        :opcoes="opcoesTipo"
        @update:model-value="trocarTipo"
      />
      <BrInput v-model="formAvaliacao.nome" rotulo="Nome" placeholder="Ex.: Prova 1" required />
      <div class="linha">
        <BrInput v-model="formAvaliacao.data" rotulo="Data (opcional)" type="date" />
        <BrInput
          v-if="formAvaliacao.tipo !== 'RECUPERACAO'"
          v-model="formAvaliacao.peso"
          rotulo="Peso"
          type="number"
          min="0.1"
          max="100"
          step="0.1"
          required
        />
      </div>
      <template v-if="formAvaliacao.tipo === 'RECUPERACAO'">
        <BrSelect
          v-model="formAvaliacao.substituicao"
          rotulo="A nota substitui (quando for maior)"
          :opcoes="opcoesSubstituicao()"
        />
        <BrSelect
          v-if="formAvaliacao.substituicao === 'AVALIACAO'"
          v-model="formAvaliacao.substitui_avaliacao_id"
          rotulo="Avaliação substituída"
          :opcoes="regularesDoCiclo.map((r) => ({ valor: r.id, rotulo: r.nome }))"
        />
        <p class="text-down-01 mb-0">
          <template v-if="formAvaliacao.substituicao === 'MELHOR'">
            Para cada estudante, o sistema escolhe a avaliação cuja troca mais aumenta a média; você
            pode mudar a escolha na planilha.
          </template>
          <template v-else-if="formAvaliacao.substituicao === 'CICLO'">
            Se for maior, a nota da recuperação passa a ser a nota do trimestre (OD art. 245).
          </template>
        </p>
      </template>
      <BrMessage v-if="erroAvaliacao" estado="danger">{{ erroAvaliacao }}</BrMessage>
    </form>
    <template #rodape>
      <BrButton variante="secondary" @click="formAvaliacao = null">Cancelar</BrButton>
      <BrButton
        type="submit"
        form="form-avaliacao"
        variante="primary"
        :carregando="salvandoAvaliacao"
      >
        Salvar
      </BrButton>
    </template>
  </BrModal>

  <ModalConfirmacao
    v-if="excluindo"
    titulo="Excluir avaliação"
    :acao="excluirAvaliacao"
    @fechar="excluindo = null"
  >
    Excluir <strong>{{ excluindo.nome }}</strong> e todas as notas lançadas nela?
  </ModalConfirmacao>
</template>

<style scoped>
.nome {
  font-weight: normal;
  white-space: nowrap;
}

.coluna-nota {
  min-width: 110px;
  text-align: center;
}

th.recuperacao,
td.recuperacao {
  background: var(--gray-5);
}

.titulo-avaliacao {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-scale-half);
}

.acoes-avaliacao {
  display: inline-flex;
}

.detalhe {
  color: var(--gray-60);
  font-weight: normal;
}

.celula {
  max-width: 80px;
  margin: 0 auto;
}

.celula input {
  text-align: center;
}

.celula.substituida input {
  text-decoration: line-through;
  color: var(--gray-50);
}

.escolha {
  display: block;
  margin: var(--spacing-scale-half) auto 0;
  max-width: 140px;
  font-size: var(--font-size-scale-down-02);
}

.abaixo {
  color: var(--danger);
}

.situacao {
  font-weight: var(--font-weight-semi-bold);
}

.situacao.aprovado {
  color: var(--success);
}

.situacao.abaixo_da_media,
.situacao.reprovado_por_falta {
  color: var(--danger);
}

.situacao.em_andamento {
  color: var(--gray-60);
}

tr.inativo th,
tr.inativo td {
  opacity: 0.6;
}

.rodape {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--background-light);
  box-shadow: 0 -2px 6px rgb(0 0 0 / 10%);
  z-index: 10;
}

.conteudo-rodape {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--spacing-scale-2x);
  max-width: 1140px;
  margin: 0 auto;
  padding: var(--spacing-scale-2x);
}
</style>
