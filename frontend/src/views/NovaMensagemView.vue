<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { api, exigir, type Estudante, type PreviaMensagem, type Turma } from '@/api/client'
import {
  BrButton,
  BrCard,
  BrCheckbox,
  BrInput,
  BrMessage,
  BrSelect,
  BrTextarea,
  type Opcao,
} from '@/components/govbr'

const route = useRoute()
const router = useRouter()

const turmas = ref<Turma[]>([])
const turmaId = ref<number | null>(null)
const estudantes = ref<Estudante[]>([])
const escolherEstudantes = ref(false)
const selecionados = ref<Set<number>>(new Set())
const incluirEstudantes = ref(true)
const incluirResponsaveis = ref(false)
const assunto = ref('')
const corpo = ref('Olá, {primeiro_nome}!\n\n')

const previa = ref<PreviaMensagem | null>(null)
const erroPrevia = ref('')
const erro = ref('')
const enviando = ref(false)

const CAMPOS = [
  { chave: '{primeiro_nome}', rotulo: 'Primeiro nome' },
  { chave: '{nome}', rotulo: 'Nome completo' },
  { chave: '{disciplina}', rotulo: 'Disciplina' },
  { chave: '{turma}', rotulo: 'Turma' },
]

const turma = computed(() => turmas.value.find((t) => t.id === turmaId.value) ?? null)
const ehEmi = computed(() => turma.value?.nivel === 'EMI')
const opcoesTurma = computed<Opcao<number>[]>(() =>
  turmas.value.map((t) => ({ valor: t.id, rotulo: `${t.disciplina} – ${t.nome}` })),
)
const ativos = computed(() => estudantes.value.filter((e) => e.ativo))

const dados = computed(() =>
  turmaId.value
    ? {
        turma_id: turmaId.value,
        estudante_ids: escolherEstudantes.value ? [...selecionados.value] : null,
        incluir_estudantes: incluirEstudantes.value,
        incluir_responsaveis: ehEmi.value && incluirResponsaveis.value,
        assunto: assunto.value.trim() || '(sem assunto)',
        corpo: corpo.value.trim() || '(sem texto)',
      }
    : null,
)

async function carregarEstudantes() {
  estudantes.value = []
  if (!turmaId.value) return
  const params = { path: { turma_id: turmaId.value } }
  estudantes.value = await exigir(api.GET('/api/turmas/{turma_id}/estudantes', { params }))
}

let temporizador: ReturnType<typeof setTimeout> | undefined
function atualizarPrevia() {
  clearTimeout(temporizador)
  temporizador = setTimeout(async () => {
    erroPrevia.value = ''
    if (!dados.value || (escolherEstudantes.value && selecionados.value.size === 0)) {
      previa.value = null
      return
    }
    try {
      previa.value = await exigir(api.POST('/api/mensagens/previa', { body: dados.value }))
    } catch (e) {
      previa.value = null
      erroPrevia.value = (e as Error).message
    }
  }, 400)
}

function alternar(id: number) {
  const novo = new Set(selecionados.value)
  if (novo.has(id)) novo.delete(id)
  else novo.add(id)
  selecionados.value = novo
}

function inserir(campo: string) {
  corpo.value = `${corpo.value}${campo}`
}

async function enviar() {
  if (!dados.value || !assunto.value.trim() || !corpo.value.trim()) {
    erro.value = 'Preencha a turma, o assunto e o texto.'
    return
  }
  enviando.value = true
  erro.value = ''
  try {
    const mensagem = await exigir(api.POST('/api/mensagens', { body: dados.value }))
    await router.push(`/mensagens/${mensagem.id}`)
  } catch (e) {
    erro.value = (e as Error).message
  } finally {
    enviando.value = false
  }
}

watch(turmaId, async () => {
  await carregarEstudantes()
  if (!route.query.estudantes) {
    escolherEstudantes.value = false
    selecionados.value = new Set()
  }
})
watch(dados, atualizarPrevia, { deep: true })

onMounted(async () => {
  try {
    turmas.value = await exigir(api.GET('/api/turmas'))
    // Atalhos: /mensagens/nova?turma=1&estudantes=3,4
    if (route.query.turma) turmaId.value = Number(route.query.turma)
    if (typeof route.query.estudantes === 'string') {
      escolherEstudantes.value = true
      selecionados.value = new Set(route.query.estudantes.split(',').map(Number))
    }
  } catch (e) {
    erro.value = (e as Error).message
  }
})
</script>

<template>
  <nav class="br-breadcrumb" aria-label="Breadcrumbs">
    <ol class="crumb-list">
      <li class="crumb"><RouterLink to="/mensagens">Mensagens</RouterLink></li>
      <li class="crumb" data-active="active">
        <i class="icon fas fa-chevron-right" aria-hidden="true"></i><span>Nova mensagem</span>
      </li>
    </ol>
  </nav>
  <h1>Nova mensagem</h1>

  <div class="layout">
    <form class="formulario" @submit.prevent="enviar">
      <BrSelect v-model="turmaId" rotulo="Turma" :opcoes="opcoesTurma" />

      <fieldset v-if="turma">
        <legend>Destinatários</legend>
        <div class="linha">
          <BrCheckbox v-model="incluirEstudantes" rotulo="Estudantes" />
          <BrCheckbox
            v-if="ehEmi"
            v-model="incluirResponsaveis"
            rotulo="Responsáveis (e-mail separado)"
          />
        </div>
        <BrCheckbox
          v-model="escolherEstudantes"
          class="mt-2"
          :rotulo="`Só alguns estudantes (senão, todos os ${ativos.length} ativos)`"
        />
        <div v-if="escolherEstudantes" class="lista-estudantes">
          <div v-for="e in estudantes" :key="e.id" class="br-checkbox">
            <input
              :id="`est-${e.id}`"
              type="checkbox"
              :checked="selecionados.has(e.id)"
              @change="alternar(e.id)"
            />
            <label :for="`est-${e.id}`">
              {{ e.nome }}
              <span v-if="!e.email" class="text-down-02 sem-email">sem e-mail</span>
            </label>
          </div>
        </div>
      </fieldset>

      <BrInput
        v-model="assunto"
        rotulo="Assunto"
        placeholder="Ex.: Prova de {disciplina}"
        required
      />
      <BrTextarea v-model="corpo" rotulo="Mensagem" :linhas="10" :maxlength="10000" />
      <div class="campos">
        <span class="text-down-01">Inserir:</span>
        <BrButton v-for="c in CAMPOS" :key="c.chave" densidade="small" @click="inserir(c.chave)">
          {{ c.rotulo }}
        </BrButton>
      </div>

      <BrMessage v-if="erro" estado="danger">{{ erro }}</BrMessage>
      <div>
        <BrButton
          type="submit"
          variante="primary"
          icone="fas fa-paper-plane"
          :carregando="enviando"
          :disabled="!previa || previa.destinatarios.length === 0"
        >
          Enviar para {{ previa?.destinatarios.length ?? 0 }} destinatário(s)
        </BrButton>
      </div>
    </form>

    <aside aria-label="Prévia">
      <BrCard>
        <template #cabecalho><strong>Prévia</strong></template>
        <p v-if="!turma" class="text-down-01 mb-0">Escolha a turma.</p>
        <BrMessage v-else-if="erroPrevia" estado="danger">{{ erroPrevia }}</BrMessage>
        <template v-else-if="previa">
          <p>
            <strong>{{ previa.destinatarios.length }}</strong> e-mail(s) serão enviados.
          </p>
          <BrMessage v-if="previa.sem_email.length" estado="warning" titulo="Sem e-mail:">
            {{ previa.sem_email.map((s) => s.nome).join(', ') }}
          </BrMessage>
          <template v-if="previa.exemplo_assunto">
            <p class="text-down-01 mb-1">Exemplo (para {{ previa.destinatarios[0]?.nome }}):</p>
            <div class="exemplo">
              <strong>{{ previa.exemplo_assunto }}</strong>
              <pre>{{ previa.exemplo_corpo }}</pre>
            </div>
          </template>
        </template>
      </BrCard>
    </aside>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: minmax(0, 3fr) minmax(0, 2fr);
  gap: var(--spacing-scale-3x);
  align-items: start;
}

@media (max-width: 768px) {
  .layout {
    grid-template-columns: 1fr;
  }
}

.lista-estudantes {
  max-height: 240px;
  overflow-y: auto;
  margin-top: var(--spacing-scale-base);
  padding: var(--spacing-scale-base);
  border: 1px solid var(--border-color);
  border-radius: var(--surface-rounder-sm, 4px);
}

.sem-email {
  color: var(--danger);
  margin-left: var(--spacing-scale-half);
}

.campos {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--spacing-scale-half);
}

.exemplo {
  padding: var(--spacing-scale-2x);
  background: var(--gray-2);
  border-radius: var(--surface-rounder-sm, 4px);
}

.exemplo pre {
  margin: var(--spacing-scale-base) 0 0;
  font-family: inherit;
  white-space: pre-wrap;
}
</style>
