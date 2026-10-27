<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'

import { api, exigir } from '@/api/client'
import CabecalhoTurma from '@/components/CabecalhoTurma.vue'
import { BrButton, BrMessage, BrTextarea } from '@/components/govbr'
import { useTurma } from '@/composables/useTurma'
import { agrupar, desagrupar, montarLinhas, paraRegistros, type Linha } from '@/utils/conteudo'
import { formatarDataCurta, hojeIso, nomeDoMes } from '@/utils/formato'

const props = defineProps<{ id: string }>()
const turmaId = computed(() => Number(props.id))
const { turma, erro: erroTurma } = useTurma(turmaId)

const linhas = ref<Linha[]>([])
const semAulas = ref(false)
const erro = ref('')
const salvando = ref(false)
const salvo = ref(false)
const alterado = ref(false)
const hoje = hojeIso()

/** Linhas com o cabeçalho do mês quando o mês muda */
const comMeses = computed(() =>
  linhas.value.map((l, i) => {
    const anterior = linhas.value[i - 1]
    const mudouMes = !anterior || anterior.inicio.slice(0, 7) !== l.inicio.slice(0, 7)
    return { linha: l, indice: i, mes: mudouMes ? nomeDoMes(l.inicio) : null }
  }),
)

function rotuloDatas(l: Linha): string {
  if (l.datas.length === 0) return `${formatarDataCurta(l.inicio)} a ${formatarDataCurta(l.fim)}`
  if (l.datas.length === 1) return formatarDataCurta(l.inicio)
  return `${formatarDataCurta(l.inicio)} a ${formatarDataCurta(l.fim)} (${l.datas.length} dias)`
}

async function carregar() {
  try {
    const params = { path: { turma_id: turmaId.value } }
    const [aulas, registros] = await Promise.all([
      exigir(api.GET('/api/turmas/{turma_id}/aulas', { params })),
      exigir(api.GET('/api/turmas/{turma_id}/conteudos', { params })),
    ])
    const dias = aulas.filter((a) => a.status !== 'CANCELADA').map((a) => a.data)
    semAulas.value = dias.length === 0
    linhas.value = montarLinhas(dias, registros)
    alterado.value = false
  } catch (e) {
    erro.value = (e as Error).message
  }
}

function editar(i: number, texto: string) {
  linhas.value[i]!.texto = texto
  alterado.value = true
  salvo.value = false
}

function unir(i: number) {
  linhas.value = agrupar(linhas.value, i)
  alterado.value = true
  salvo.value = false
}

function separar(i: number) {
  linhas.value = desagrupar(linhas.value, i)
  alterado.value = true
  salvo.value = false
}

async function salvar() {
  salvando.value = true
  erro.value = ''
  try {
    const params = { path: { turma_id: turmaId.value } }
    const body = paraRegistros(linhas.value)
    await exigir(api.PUT('/api/turmas/{turma_id}/conteudos', { params, body }))
    alterado.value = false
    salvo.value = true
  } catch (e) {
    erro.value = (e as Error).message
  } finally {
    salvando.value = false
  }
}

function avisarAoSair(evento: BeforeUnloadEvent) {
  if (alterado.value) evento.preventDefault()
}

onBeforeRouteLeave(() =>
  alterado.value ? window.confirm('Há alterações não salvas no conteúdo. Sair mesmo assim?') : true,
)
onMounted(() => {
  carregar()
  window.addEventListener('beforeunload', avisarAoSair)
})
onBeforeUnmount(() => window.removeEventListener('beforeunload', avisarAoSair))
</script>

<template>
  <BrMessage v-if="erroTurma" estado="danger">{{ erroTurma }}</BrMessage>

  <template v-if="turma">
    <CabecalhoTurma :turma="turma" aba="conteudo" />

    <p class="text-down-01">
      Um campo por dia de aula do período. Preencha quando quiser, inclusive o planejamento do ano
      todo. Use <i class="fas fa-link" aria-hidden="true"></i> para juntar um dia ao seguinte num só
      registro e <i class="fas fa-unlink" aria-hidden="true"></i> para separar.
    </p>

    <BrMessage v-if="semAulas" estado="info" titulo="Nenhuma aula no calendário.">
      Gere o calendário na aba
      <RouterLink :to="`/turmas/${turma.id}/aulas`">Aulas e chamada</RouterLink> para listar os dias
      aqui.
    </BrMessage>

    <ol class="linhas">
      <template v-for="{ linha, indice, mes } in comMeses" :key="`${linha.inicio}-${indice}`">
        <li v-if="mes" class="mes" aria-hidden="true">{{ mes }}</li>
        <li
          class="linha"
          :class="{ grupo: linha.datas.length > 1, hoje: linha.datas.includes(hoje) }"
        >
          <div class="datas">
            {{ rotuloDatas(linha) }}
            <span v-if="linha.datas.length === 0" class="text-down-02 aviso">
              sem aulas neste intervalo
            </span>
          </div>
          <BrTextarea
            :model-value="linha.texto"
            :rotulo="`Conteúdo de ${rotuloDatas(linha)}`"
            rotulo-oculto
            :maxlength="2000"
            placeholder="O que foi ou será trabalhado"
            @update:model-value="editar(indice, $event)"
          />
          <div class="acoes">
            <BrButton
              v-if="linha.datas.length > 1"
              circular
              densidade="small"
              icone="fas fa-unlink"
              :rotulo="`Separar ${rotuloDatas(linha)} em dias`"
              @click="separar(indice)"
            />
            <BrButton
              v-if="indice < linhas.length - 1"
              circular
              densidade="small"
              icone="fas fa-link"
              :rotulo="`Juntar ${rotuloDatas(linha)} com o dia seguinte`"
              @click="unir(indice)"
            />
          </div>
        </li>
      </template>
    </ol>

    <div v-if="linhas.length" class="rodape">
      <div class="conteudo-rodape">
        <span v-if="erro" class="text-danger">{{ erro }}</span>
        <span v-else-if="alterado" class="text-down-01">Alterações não salvas</span>
        <span v-else-if="salvo" class="text-down-01">
          <i class="fas fa-check" aria-hidden="true"></i> Salvo
        </span>
        <BrButton
          variante="primary"
          icone="fas fa-save"
          :carregando="salvando"
          :disabled="!alterado"
          @click="salvar"
        >
          Salvar conteúdo
        </BrButton>
      </div>
    </div>
  </template>
</template>

<style scoped>
.linhas {
  list-style: none;
  margin: 0;
  padding: 0 0 96px;
}

.mes {
  margin: var(--spacing-scale-3x) 0 var(--spacing-scale-base);
  font-weight: var(--font-weight-semi-bold);
  color: var(--gray-60);
}

.linha {
  display: grid;
  grid-template-columns: 200px 1fr auto;
  align-items: start;
  gap: var(--spacing-scale-2x);
  padding: var(--spacing-scale-base) var(--spacing-scale-2x);
  background: var(--background-light);
  border-bottom: 1px solid var(--border-color);
}

.linha.grupo {
  box-shadow: inset 4px 0 0 var(--interactive);
}

.linha.hoje .datas {
  color: var(--interactive);
  font-weight: var(--font-weight-semi-bold);
}

.datas {
  padding-top: var(--spacing-scale-base);
}

.aviso {
  display: block;
  color: var(--warning-dark, var(--danger));
}

.acoes {
  display: flex;
  gap: var(--spacing-scale-half);
  min-width: 72px;
  justify-content: flex-end;
}

@media (max-width: 576px) {
  .linha {
    grid-template-columns: 1fr auto;
  }

  .linha .br-textarea {
    grid-column: 1 / -1;
    grid-row: 2;
  }
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
