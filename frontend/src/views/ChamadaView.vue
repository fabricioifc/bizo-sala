<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { api, exigir, type Alerta, type Chamada } from '@/api/client'
import { BrButton, BrMessage } from '@/components/govbr'
import { carregarChamada, salvarChamada } from '@/offline/chamadas'
import { useAlertasStore } from '@/stores/alertas'
import { useSincronizacaoStore } from '@/stores/sincronizacao'
import { descreverAlerta } from '@/utils/alertas'
import { formatarDataCurta } from '@/utils/formato'

const props = defineProps<{ id: string }>()
const aulaId = computed(() => Number(props.id))
const sincronizacao = useSincronizacaoStore()
const loja = useAlertasStore()

/** Alertas ao SISAE que esta chamada acabou de gerar */
const novosAlertas = ref<Alerta[]>([])

async function verificarAlertas(turmaId: number, data: string) {
  try {
    const query = { status: 'PENDENTE' as const, turma_id: turmaId }
    const pendentes = await exigir(api.GET('/api/alertas', { params: { query } }))
    novosAlertas.value = pendentes.filter((a) => a.data_gatilho === data)
    await loja.atualizar()
  } catch {
    novosAlertas.value = []
  }
}

const chamada = ref<Chamada | null>(null)
/** Faltas por estudante (em horas-aula) */
const faltas = ref<Record<number, number>>({})
const offline = ref(false)
const tinhaPendente = ref(false)
const erro = ref('')
const salvando = ref(false)
const resultado = ref<'enviada' | 'pendente' | null>(null)
const alterada = ref(false)

const horas = computed(() => chamada.value?.aula.horas_aula ?? 1)
const opcoes = computed(() => Array.from({ length: horas.value + 1 }, (_, i) => i))
const comFalta = computed(() => Object.values(faltas.value).filter((f) => f > 0).length)
const cancelada = computed(() => chamada.value?.aula.status === 'CANCELADA')

function rotulo(n: number) {
  return n === 0 ? 'P' : String(n)
}

function descricao(n: number) {
  if (n === 0) return 'presente'
  return n === horas.value ? `faltou as ${n} aulas` : `${n} falta${n > 1 ? 's' : ''}`
}

function marcar(estudanteId: number, n: number) {
  faltas.value[estudanteId] = n
  alterada.value = true
  resultado.value = null
}

function todosPresentes() {
  for (const id of Object.keys(faltas.value)) faltas.value[Number(id)] = 0
  alterada.value = true
  resultado.value = null
}

async function carregar() {
  try {
    const r = await carregarChamada(aulaId.value)
    chamada.value = r.dados
    offline.value = r.offline
    tinhaPendente.value = r.pendente !== null
    const pendentes = new Map(r.pendente?.map((p) => [p.estudante_id, p.faltas]))
    // Sem registro = presente (as aulas passadas ficam em aberto até a chamada ser salva)
    faltas.value = Object.fromEntries(
      r.dados.estudantes.map((e) => [
        e.estudante_id,
        pendentes.get(e.estudante_id) ?? e.faltas ?? 0,
      ]),
    )
  } catch (e) {
    erro.value = (e as Error).message
  }
}

async function salvar() {
  salvando.value = true
  erro.value = ''
  try {
    const registros = Object.entries(faltas.value).map(([id, n]) => ({
      estudante_id: Number(id),
      faltas: n,
    }))
    resultado.value = await salvarChamada(aulaId.value, registros)
    alterada.value = false
    if (chamada.value && resultado.value === 'enviada') {
      chamada.value.aula.status = 'DADA'
      await verificarAlertas(chamada.value.aula.turma_id, chamada.value.aula.data)
    }
  } catch (e) {
    erro.value = (e as Error).message
  } finally {
    salvando.value = false
    await sincronizacao.atualizar()
  }
}

onMounted(carregar)
</script>

<template>
  <div class="chamada">
    <RouterLink
      v-if="chamada"
      :to="`/turmas/${chamada.aula.turma_id}/aulas`"
      class="br-button small voltar"
    >
      <i class="fas fa-arrow-left" aria-hidden="true"></i> Aulas da turma
    </RouterLink>

    <BrMessage v-if="erro" estado="danger">{{ erro }}</BrMessage>

    <template v-if="chamada">
      <h1 class="mb-0">{{ chamada.disciplina }} – {{ chamada.turma_nome }}</h1>
      <p class="text-down-01">
        {{ formatarDataCurta(chamada.aula.data) }} · {{ horas }} hora{{ horas > 1 ? 's' : '' }}-aula
        <span v-if="chamada.aula.status === 'DADA'"> · chamada já registrada</span>
      </p>

      <BrMessage v-if="offline" estado="warning" titulo="Sem conexão.">
        Mostrando a lista guardada no aparelho. A chamada será enviada quando a conexão voltar.
      </BrMessage>
      <BrMessage v-if="tinhaPendente" estado="info">
        Há alterações desta chamada guardadas no aparelho, ainda não enviadas.
      </BrMessage>
      <BrMessage v-if="cancelada" estado="warning" titulo="Aula cancelada.">
        Reabra a aula na tela de aulas da turma para fazer a chamada.
      </BrMessage>

      <template v-else>
        <div class="barra">
          <span>
            <strong>{{ chamada.estudantes.length - comFalta }}</strong> presentes ·
            <strong>{{ comFalta }}</strong> com falta
          </span>
          <BrButton densidade="small" icone="fas fa-check-double" @click="todosPresentes">
            Todos presentes
          </BrButton>
        </div>

        <BrMessage v-if="chamada.estudantes.length === 0" estado="info">
          Nenhum estudante ativo matriculado nesta turma.
        </BrMessage>

        <ul class="lista">
          <li
            v-for="e in chamada.estudantes"
            :key="e.estudante_id"
            :class="{ falta: faltas[e.estudante_id]! > 0 }"
          >
            <span :id="`nome-${e.estudante_id}`" class="nome">{{ e.nome }}</span>
            <div class="opcoes" role="radiogroup" :aria-labelledby="`nome-${e.estudante_id}`">
              <button
                v-for="n in opcoes"
                :key="n"
                type="button"
                role="radio"
                class="br-button small circle"
                :class="
                  faltas[e.estudante_id] === n ? (n === 0 ? 'primary' : 'falta') : 'secondary'
                "
                :aria-checked="faltas[e.estudante_id] === n"
                :aria-label="descricao(n)"
                :title="descricao(n)"
                @click="marcar(e.estudante_id, n)"
              >
                {{ rotulo(n) }}
              </button>
            </div>
          </li>
        </ul>

        <div class="rodape">
          <BrMessage v-if="resultado === 'enviada'" estado="success">Chamada salva.</BrMessage>
          <BrMessage
            v-if="resultado === 'enviada' && novosAlertas.length"
            estado="warning"
            titulo="Avisar o SISAE:"
          >
            {{ novosAlertas.map((a) => `${a.estudante_nome} (${descreverAlerta(a)})`).join('; ') }}.
            <RouterLink to="/alertas">Ver alertas</RouterLink>
          </BrMessage>
          <BrMessage v-if="resultado === 'pendente'" estado="warning">
            Sem conexão: chamada guardada no aparelho. Ela será enviada automaticamente quando a
            internet voltar.
          </BrMessage>
          <BrButton
            variante="primary"
            bloco
            icone="fas fa-save"
            :carregando="salvando"
            :disabled="chamada.estudantes.length === 0"
            @click="salvar"
          >
            {{ alterada || chamada.aula.status !== 'DADA' ? 'Salvar chamada' : 'Salvar novamente' }}
          </BrButton>
        </div>
      </template>
    </template>
  </div>
</template>

<style scoped>
.chamada {
  max-width: 640px;
  margin: 0 auto;
  padding-bottom: 120px;
}

.voltar {
  margin-bottom: var(--spacing-scale-2x);
}

.barra {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-scale-2x);
  margin: var(--spacing-scale-2x) 0;
}

.lista {
  list-style: none;
  margin: 0;
  padding: 0;
  background: var(--background-light);
  border-radius: var(--surface-rounder-md, 8px);
}

.lista li {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-scale-2x);
  padding: var(--spacing-scale-base) var(--spacing-scale-2x);
  border-bottom: 1px solid var(--border-color);
}

.lista li.falta {
  background: var(--red-warm-vivid-5, #fde0db);
}

.nome {
  font-size: var(--font-size-scale-up-01);
}

.opcoes {
  display: flex;
  flex-shrink: 0;
  gap: var(--spacing-scale-half);
}

.opcoes .falta {
  background: var(--danger);
  color: var(--pure-0, #fff);
}

/* Botão de salvar sempre visível no celular */
.rodape {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: var(--spacing-scale-2x);
  background: var(--background-light);
  box-shadow: 0 -2px 6px rgb(0 0 0 / 10%);
  z-index: 10;
}

.rodape > * {
  max-width: 640px;
  margin: 0 auto var(--spacing-scale-base);
}
</style>
