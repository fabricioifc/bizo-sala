<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'

import { api, exigir, type DiaNaoLetivo } from '@/api/client'
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
import { DIAS_SEMANA, formatarData } from '@/utils/formato'

const anoAtual = new Date().getFullYear()
const ano = ref<number | null>(anoAtual)
const opcoesAno: Opcao<number>[] = [anoAtual - 1, anoAtual, anoAtual + 1].map((a) => ({
  valor: a,
  rotulo: String(a),
}))

const dias = ref<DiaNaoLetivo[]>([])
const erroCarga = ref('')

const formulario = ref<{ data: string; descricao: string } | null>(null)
const editandoId = ref<number | null>(null)
const salvando = ref(false)
const erroForm = ref('')
const excluindo = ref<DiaNaoLetivo | null>(null)

const diaDaSemana = (iso: string) => DIAS_SEMANA[(new Date(`${iso}T12:00:00`).getDay() + 6) % 7]
const titulo = computed(() => `Dias não letivos de ${ano.value ?? ''}`)

async function carregar() {
  try {
    const query = ano.value ? { ano: ano.value } : {}
    dias.value = await exigir(api.GET('/api/dias-nao-letivos', { params: { query } }))
  } catch (e) {
    erroCarga.value = (e as Error).message
  }
}

function novo() {
  editandoId.value = null
  erroForm.value = ''
  formulario.value = { data: '', descricao: '' }
}

function editar(dia: DiaNaoLetivo) {
  editandoId.value = dia.id
  erroForm.value = ''
  formulario.value = { data: dia.data, descricao: dia.descricao }
}

async function salvar() {
  if (!formulario.value) return
  salvando.value = true
  erroForm.value = ''
  try {
    const body = formulario.value
    if (editandoId.value === null) {
      await exigir(api.POST('/api/dias-nao-letivos', { body }))
    } else {
      const params = { path: { dia_id: editandoId.value } }
      await exigir(api.PUT('/api/dias-nao-letivos/{dia_id}', { params, body }))
    }
    formulario.value = null
    await carregar()
  } catch (e) {
    erroForm.value = (e as Error).message
  } finally {
    salvando.value = false
  }
}

async function excluir() {
  if (!excluindo.value) return
  const params = { path: { dia_id: excluindo.value.id } }
  await exigir(api.DELETE('/api/dias-nao-letivos/{dia_id}', { params }))
  await carregar()
}

watch(ano, carregar)
onMounted(carregar)
</script>

<template>
  <h1>Dias não letivos</h1>
  <p class="text-down-01">
    Feriados, recessos e outros dias sem aula. Eles são descontados da projeção de carga horária de
    todas as turmas.
  </p>
  <BrMessage v-if="erroCarga" estado="danger">{{ erroCarga }}</BrMessage>

  <BrTable :titulo="titulo" :vazia="dias.length === 0">
    <template #acoes>
      <BrSelect v-model="ano" rotulo="Ano" :opcoes="opcoesAno" class="filtro-ano" />
      <BrButton variante="primary" icone="fas fa-plus" @click="novo">Novo dia</BrButton>
    </template>
    <thead>
      <tr>
        <th scope="col">Data</th>
        <th scope="col">Dia da semana</th>
        <th scope="col">Descrição</th>
        <th scope="col"><span class="sr-only">Ações</span></th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="dia in dias" :key="dia.id">
        <td>{{ formatarData(dia.data) }}</td>
        <td>{{ diaDaSemana(dia.data) }}</td>
        <td>{{ dia.descricao }}</td>
        <td class="text-right text-nowrap">
          <BrButton
            circular
            icone="fas fa-pen"
            :rotulo="`Editar ${formatarData(dia.data)}`"
            @click="editar(dia)"
          />
          <BrButton
            circular
            icone="fas fa-trash"
            :rotulo="`Excluir ${formatarData(dia.data)}`"
            @click="excluindo = dia"
          />
        </td>
      </tr>
    </tbody>
  </BrTable>

  <BrModal
    v-if="formulario"
    :titulo="editandoId === null ? 'Novo dia não letivo' : 'Editar dia não letivo'"
    tamanho="small"
    @fechar="formulario = null"
  >
    <form id="form-dia" class="formulario" @submit.prevent="salvar">
      <BrInput v-model="formulario.data" rotulo="Data" type="date" required />
      <BrInput
        v-model="formulario.descricao"
        rotulo="Descrição"
        placeholder="Ex.: Feriado de Tiradentes"
        required
      />
      <BrMessage v-if="erroForm" estado="danger">{{ erroForm }}</BrMessage>
    </form>
    <template #rodape>
      <BrButton variante="secondary" @click="formulario = null">Cancelar</BrButton>
      <BrButton type="submit" form="form-dia" variante="primary" :carregando="salvando">
        Salvar
      </BrButton>
    </template>
  </BrModal>

  <ModalConfirmacao
    v-if="excluindo"
    titulo="Excluir dia não letivo"
    :acao="excluir"
    @fechar="excluindo = null"
  >
    Excluir <strong>{{ formatarData(excluindo.data) }} – {{ excluindo.descricao }}</strong
    >?
  </ModalConfirmacao>
</template>

<style scoped>
.filtro-ano {
  min-width: 140px;
}
</style>
