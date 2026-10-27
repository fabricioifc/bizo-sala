<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api, exigir, type Curso, type CursoEntrada, type Nivel } from '@/api/client'
import ModalConfirmacao from '@/components/ModalConfirmacao.vue'
import {
  BrButton,
  BrCheckbox,
  BrInput,
  BrMessage,
  BrModal,
  BrSelect,
  BrTable,
  type Opcao,
} from '@/components/govbr'
import { formatarNumero, NIVEIS, REGIMES } from '@/utils/formato'
import { numeroOuNulo } from '@/utils/formulario'

const cursos = ref<Curso[]>([])
const erroCarga = ref('')

const formulario = ref<CursoEntrada | null>(null)
const editandoId = ref<number | null>(null)
const salvando = ref(false)
const erroForm = ref('')
const excluindo = ref<Curso | null>(null)

const opcoesNivel: Opcao<Nivel>[] = [
  { valor: 'EMI', rotulo: NIVEIS.EMI },
  { valor: 'GRADUACAO', rotulo: NIVEIS.GRADUACAO },
]

/** Valores padrão conforme a Organização Didática do IFC e a regra do professor */
function padrao(nivel: Nivel): CursoEntrada {
  return nivel === 'EMI'
    ? {
        nome: '',
        nivel,
        regime: 'ANUAL',
        media_aprovacao: 6,
        exame_final: false,
        alerta_faltas_consecutivas: 2,
        alerta_faltas_alternadas: 5,
      }
    : {
        nome: '',
        nivel,
        regime: 'SEMESTRAL',
        media_aprovacao: 6,
        exame_final: false,
        alerta_faltas_consecutivas: null,
        alerta_faltas_alternadas: null,
      }
}

async function carregar() {
  try {
    cursos.value = await exigir(api.GET('/api/cursos'))
  } catch (e) {
    erroCarga.value = (e as Error).message
  }
}

function novo() {
  editandoId.value = null
  erroForm.value = ''
  formulario.value = padrao('EMI')
}

function editar(curso: Curso) {
  editandoId.value = curso.id
  erroForm.value = ''
  formulario.value = {
    nome: curso.nome,
    nivel: curso.nivel,
    regime: curso.regime,
    media_aprovacao: curso.media_aprovacao,
    exame_final: curso.exame_final,
    alerta_faltas_consecutivas: curso.alerta_faltas_consecutivas,
    alerta_faltas_alternadas: curso.alerta_faltas_alternadas,
  }
}

function trocarNivel(nivel: Nivel | null) {
  if (!formulario.value || !nivel) return
  const nome = formulario.value.nome
  formulario.value = { ...padrao(nivel), nome }
}

async function salvar() {
  if (!formulario.value) return
  salvando.value = true
  erroForm.value = ''
  try {
    const body = {
      ...formulario.value,
      alerta_faltas_consecutivas: numeroOuNulo(formulario.value.alerta_faltas_consecutivas),
      alerta_faltas_alternadas: numeroOuNulo(formulario.value.alerta_faltas_alternadas),
    }
    if (editandoId.value === null) {
      await exigir(api.POST('/api/cursos', { body }))
    } else {
      const params = { path: { curso_id: editandoId.value } }
      await exigir(api.PUT('/api/cursos/{curso_id}', { params, body }))
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
  const params = { path: { curso_id: excluindo.value.id } }
  await exigir(api.DELETE('/api/cursos/{curso_id}', { params }))
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <h1>Cursos</h1>
  <BrMessage v-if="erroCarga" estado="danger">{{ erroCarga }}</BrMessage>

  <BrTable titulo="Cursos cadastrados" :vazia="cursos.length === 0">
    <template #acoes>
      <BrButton variante="primary" icone="fas fa-plus" @click="novo">Novo curso</BrButton>
    </template>
    <thead>
      <tr>
        <th scope="col">Nome</th>
        <th scope="col">Nível</th>
        <th scope="col">Regime</th>
        <th scope="col">Média</th>
        <th scope="col">Alerta SISAE</th>
        <th scope="col"><span class="sr-only">Ações</span></th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="curso in cursos" :key="curso.id">
        <td>{{ curso.nome }}</td>
        <td>{{ NIVEIS[curso.nivel] }}</td>
        <td>{{ REGIMES[curso.regime] }}</td>
        <td>{{ formatarNumero(curso.media_aprovacao) }}</td>
        <td>
          <template v-if="curso.alerta_faltas_consecutivas || curso.alerta_faltas_alternadas">
            <span v-if="curso.alerta_faltas_consecutivas">
              {{ curso.alerta_faltas_consecutivas }} consecutivas
            </span>
            <span v-if="curso.alerta_faltas_consecutivas && curso.alerta_faltas_alternadas">
              ·
            </span>
            <span v-if="curso.alerta_faltas_alternadas">
              {{ curso.alerta_faltas_alternadas }} alternadas
            </span>
          </template>
          <template v-else>—</template>
        </td>
        <td class="text-right text-nowrap">
          <BrButton
            circular
            icone="fas fa-pen"
            :rotulo="`Editar ${curso.nome}`"
            @click="editar(curso)"
          />
          <BrButton
            circular
            icone="fas fa-trash"
            :rotulo="`Excluir ${curso.nome}`"
            @click="excluindo = curso"
          />
        </td>
      </tr>
    </tbody>
  </BrTable>

  <BrModal
    v-if="formulario"
    :titulo="editandoId === null ? 'Novo curso' : 'Editar curso'"
    @fechar="formulario = null"
  >
    <form id="form-curso" class="formulario" @submit.prevent="salvar">
      <BrInput v-model="formulario.nome" rotulo="Nome do curso" required />
      <BrSelect
        :model-value="formulario.nivel"
        rotulo="Nível"
        :opcoes="opcoesNivel"
        :disabled="editandoId !== null"
        @update:model-value="trocarNivel"
      />
      <p class="text-down-01 mb-0">
        Regime: <strong>{{ REGIMES[formulario.regime] }}</strong>
      </p>
      <div class="linha">
        <BrInput
          v-model="formulario.media_aprovacao"
          rotulo="Média para aprovação"
          type="number"
          min="0"
          max="10"
          step="0.1"
          required
        />
        <BrCheckbox v-model="formulario.exame_final" rotulo="Possui exame final" />
      </div>
      <fieldset v-if="formulario.nivel === 'EMI'" class="linha">
        <legend>Alerta ao SISAE (faltas em encontros)</legend>
        <BrInput
          v-model="formulario.alerta_faltas_consecutivas"
          rotulo="Consecutivas"
          type="number"
          min="1"
          max="20"
        />
        <BrInput
          v-model="formulario.alerta_faltas_alternadas"
          rotulo="Alternadas"
          type="number"
          min="1"
          max="50"
        />
      </fieldset>
      <BrMessage v-if="erroForm" estado="danger">{{ erroForm }}</BrMessage>
    </form>
    <template #rodape>
      <BrButton variante="secondary" @click="formulario = null">Cancelar</BrButton>
      <BrButton type="submit" form="form-curso" variante="primary" :carregando="salvando">
        Salvar
      </BrButton>
    </template>
  </BrModal>

  <ModalConfirmacao
    v-if="excluindo"
    titulo="Excluir curso"
    :acao="excluir"
    @fechar="excluindo = null"
  >
    Excluir o curso <strong>{{ excluindo.nome }}</strong
    >?
  </ModalConfirmacao>
</template>
