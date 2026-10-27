<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { api, exigir, type Estudante, type EstudanteEntrada, type Turma } from '@/api/client'
import CabecalhoTurma from '@/components/CabecalhoTurma.vue'
import ImportarEstudantes from '@/components/ImportarEstudantes.vue'
import ModalConfirmacao from '@/components/ModalConfirmacao.vue'
import { BrButton, BrCheckbox, BrInput, BrMessage, BrModal, BrTable } from '@/components/govbr'
import { formatarData } from '@/utils/formato'
import { textoOuNulo } from '@/utils/formulario'

const props = defineProps<{ id: string }>()
const turmaId = computed(() => Number(props.id))

const turma = ref<Turma | null>(null)
const estudantes = ref<Estudante[]>([])
const erroCarga = ref('')

const formulario = ref<EstudanteEntrada | null>(null)
const editandoId = ref<number | null>(null)
const salvando = ref(false)
const erroForm = ref('')
const removendo = ref<Estudante | null>(null)
const importando = ref(false)

const ehEmi = computed(() => turma.value?.nivel === 'EMI')
const ativos = computed(() => estudantes.value.filter((e) => e.ativo).length)

async function carregar() {
  try {
    const params = { path: { turma_id: turmaId.value } }
    ;[turma.value, estudantes.value] = await Promise.all([
      exigir(api.GET('/api/turmas/{turma_id}', { params })),
      exigir(api.GET('/api/turmas/{turma_id}/estudantes', { params })),
    ])
  } catch (e) {
    erroCarga.value = (e as Error).message
  }
}

function novo() {
  editandoId.value = null
  erroForm.value = ''
  formulario.value = {
    nome: '',
    matricula: '',
    email: '',
    data_nascimento: '',
    email_responsavel: '',
    ativo: true,
  }
}

function editar(estudante: Estudante) {
  editandoId.value = estudante.id
  erroForm.value = ''
  formulario.value = {
    nome: estudante.nome,
    matricula: estudante.matricula,
    email: estudante.email ?? '',
    data_nascimento: estudante.data_nascimento ?? '',
    email_responsavel: estudante.email_responsavel ?? '',
    ativo: estudante.ativo,
  }
}

async function salvar() {
  const f = formulario.value
  if (!f) return
  salvando.value = true
  erroForm.value = ''
  try {
    const body = {
      ...f,
      email: textoOuNulo(f.email),
      data_nascimento: textoOuNulo(f.data_nascimento),
      email_responsavel: textoOuNulo(f.email_responsavel),
    }
    if (editandoId.value === null) {
      const params = { path: { turma_id: turmaId.value } }
      await exigir(api.POST('/api/turmas/{turma_id}/estudantes', { params, body }))
    } else {
      const params = { path: { estudante_id: editandoId.value } }
      await exigir(api.PUT('/api/estudantes/{estudante_id}', { params, body }))
    }
    formulario.value = null
    await carregar()
  } catch (e) {
    erroForm.value = (e as Error).message
  } finally {
    salvando.value = false
  }
}

async function remover() {
  if (!removendo.value) return
  const params = { path: { turma_id: turmaId.value, estudante_id: removendo.value.id } }
  await exigir(api.DELETE('/api/turmas/{turma_id}/estudantes/{estudante_id}', { params }))
  await carregar()
}

async function aoImportar() {
  importando.value = false
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <BrMessage v-if="erroCarga" estado="danger">{{ erroCarga }}</BrMessage>

  <template v-if="turma">
    <CabecalhoTurma :turma="turma" aba="estudantes" />

    <BrTable
      :titulo="`Estudantes (${ativos} ativos)`"
      :vazia="estudantes.length === 0"
      mensagem-vazia="Nenhum estudante matriculado. Adicione um a um ou importe uma planilha CSV."
    >
      <template #acoes>
        <RouterLink
          v-if="estudantes.length"
          :to="`/mensagens/nova?turma=${turma.id}`"
          class="br-button"
        >
          <i class="fas fa-envelope" aria-hidden="true"></i> E-mail para a turma
        </RouterLink>
        <BrButton icone="fas fa-file-import" @click="importando = true">Importar CSV</BrButton>
        <BrButton variante="primary" icone="fas fa-plus" @click="novo">Adicionar</BrButton>
      </template>
      <thead>
        <tr>
          <th scope="col">Nome</th>
          <th scope="col">Matrícula</th>
          <th scope="col">E-mail</th>
          <th v-if="ehEmi" scope="col">Nascimento</th>
          <th v-if="ehEmi" scope="col">E-mail do responsável</th>
          <th scope="col"><span class="sr-only">Ações</span></th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="e in estudantes" :key="e.id" :class="{ inativo: !e.ativo }">
          <td>
            {{ e.nome }}
            <span v-if="!e.ativo" class="br-tag text small ml-1">Inativo</span>
          </td>
          <td>{{ e.matricula }}</td>
          <td>{{ e.email ?? '—' }}</td>
          <td v-if="ehEmi">{{ formatarData(e.data_nascimento) || '—' }}</td>
          <td v-if="ehEmi">{{ e.email_responsavel ?? '—' }}</td>
          <td class="text-right text-nowrap">
            <RouterLink
              v-if="e.email || e.email_responsavel"
              :to="`/mensagens/nova?turma=${turma.id}&estudantes=${e.id}`"
              class="br-button circle"
              :aria-label="`Enviar e-mail para ${e.nome}`"
              :title="`Enviar e-mail para ${e.nome}`"
            >
              <i class="fas fa-envelope" aria-hidden="true"></i>
            </RouterLink>
            <BrButton circular icone="fas fa-pen" :rotulo="`Editar ${e.nome}`" @click="editar(e)" />
            <BrButton
              circular
              icone="fas fa-user-minus"
              :rotulo="`Remover ${e.nome} da turma`"
              @click="removendo = e"
            />
          </td>
        </tr>
      </tbody>
    </BrTable>
  </template>

  <BrModal
    v-if="formulario"
    :titulo="editandoId === null ? 'Adicionar estudante' : 'Editar estudante'"
    @fechar="formulario = null"
  >
    <form id="form-estudante" class="formulario" @submit.prevent="salvar">
      <BrInput v-model="formulario.nome" rotulo="Nome completo" required />
      <div class="linha">
        <BrInput v-model="formulario.matricula" rotulo="Matrícula" required />
        <BrInput v-model="formulario.data_nascimento" rotulo="Data de nascimento" type="date" />
      </div>
      <BrInput v-model="formulario.email" rotulo="E-mail" type="email" />
      <BrInput
        v-if="ehEmi"
        v-model="formulario.email_responsavel"
        rotulo="E-mail do responsável"
        type="email"
      />
      <BrCheckbox
        v-model="formulario.ativo"
        rotulo="Ativo (desmarque para trancamento ou transferência)"
      />
      <p v-if="editandoId !== null" class="text-down-01 mb-0">
        Os dados do estudante são os mesmos em todas as turmas em que ele estiver matriculado.
      </p>
      <BrMessage v-if="erroForm" estado="danger">{{ erroForm }}</BrMessage>
    </form>
    <template #rodape>
      <BrButton variante="secondary" @click="formulario = null">Cancelar</BrButton>
      <BrButton type="submit" form="form-estudante" variante="primary" :carregando="salvando">
        Salvar
      </BrButton>
    </template>
  </BrModal>

  <ModalConfirmacao
    v-if="removendo"
    titulo="Remover da turma"
    rotulo-confirmar="Remover"
    :acao="remover"
    @fechar="removendo = null"
  >
    Remover <strong>{{ removendo.nome }}</strong> desta turma? O cadastro do estudante é mantido.
  </ModalConfirmacao>

  <ImportarEstudantes
    v-if="importando && turma"
    :turma-id="turma.id"
    :mostrar-responsavel="ehEmi"
    @fechar="importando = false"
    @importado="aoImportar"
  />
</template>

<style scoped>
.inativo td {
  color: var(--gray-50);
}
</style>
