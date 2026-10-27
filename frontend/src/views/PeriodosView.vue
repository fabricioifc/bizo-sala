<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api, exigir, type Periodo, type PeriodoEntrada, type Regime } from '@/api/client'
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
import { formatarData, REGIMES } from '@/utils/formato'
import { textoOuNulo } from '@/utils/formulario'

const periodos = ref<Periodo[]>([])
const erroCarga = ref('')

const formulario = ref<PeriodoEntrada | null>(null)
const editandoId = ref<number | null>(null)
const salvando = ref(false)
const erroForm = ref('')
const excluindo = ref<Periodo | null>(null)

const opcoesRegime: Opcao<Regime>[] = [
  { valor: 'ANUAL', rotulo: 'Anual (EMI, 3 trimestres)' },
  { valor: 'SEMESTRAL', rotulo: 'Semestral (graduação)' },
]
const opcoesSemestre: Opcao<1 | 2>[] = [
  { valor: 1, rotulo: '1º semestre' },
  { valor: 2, rotulo: '2º semestre' },
]

const cicloVazio = () => ({ nome: '', data_inicio: '', data_fim: '' })

function padrao(regime: Regime): PeriodoEntrada {
  const ano = new Date().getFullYear()
  return {
    nome: regime === 'ANUAL' ? String(ano) : `${ano}/1`,
    regime,
    ano,
    semestre: regime === 'ANUAL' ? null : 1,
    data_inicio: '',
    data_fim: '',
    ciclos: regime === 'ANUAL' ? [cicloVazio(), cicloVazio(), cicloVazio()] : [cicloVazio()],
  }
}

async function carregar() {
  try {
    periodos.value = await exigir(api.GET('/api/periodos'))
  } catch (e) {
    erroCarga.value = (e as Error).message
  }
}

function novo() {
  editandoId.value = null
  erroForm.value = ''
  formulario.value = padrao('ANUAL')
}

function editar(periodo: Periodo) {
  editandoId.value = periodo.id
  erroForm.value = ''
  formulario.value = {
    nome: periodo.nome,
    regime: periodo.regime,
    ano: periodo.ano,
    semestre: periodo.semestre as 1 | 2 | null,
    data_inicio: periodo.data_inicio,
    data_fim: periodo.data_fim,
    ciclos: periodo.ciclos.map(({ nome, data_inicio, data_fim }) => ({
      nome,
      data_inicio,
      data_fim,
    })),
  }
}

function trocarRegime(regime: Regime | null) {
  if (formulario.value && regime && regime !== formulario.value.regime) {
    formulario.value = padrao(regime)
  }
}

/** No período semestral, o nome padrão acompanha ano/semestre */
function atualizarNomeSemestral() {
  const f = formulario.value
  if (f?.regime === 'SEMESTRAL' && editandoId.value === null) {
    f.nome = `${f.ano}/${f.semestre ?? 1}`
  }
}

async function salvar() {
  if (!formulario.value) return
  salvando.value = true
  erroForm.value = ''
  try {
    const body = {
      ...formulario.value,
      ciclos: formulario.value.ciclos.map((c) => ({ ...c, nome: textoOuNulo(c.nome) })),
    }
    if (editandoId.value === null) {
      await exigir(api.POST('/api/periodos', { body }))
    } else {
      const params = { path: { periodo_id: editandoId.value } }
      await exigir(api.PUT('/api/periodos/{periodo_id}', { params, body }))
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
  const params = { path: { periodo_id: excluindo.value.id } }
  await exigir(api.DELETE('/api/periodos/{periodo_id}', { params }))
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <h1>Períodos letivos</h1>
  <BrMessage v-if="erroCarga" estado="danger">{{ erroCarga }}</BrMessage>

  <BrTable titulo="Períodos cadastrados" :vazia="periodos.length === 0">
    <template #acoes>
      <BrButton variante="primary" icone="fas fa-plus" @click="novo">Novo período</BrButton>
    </template>
    <thead>
      <tr>
        <th scope="col">Nome</th>
        <th scope="col">Regime</th>
        <th scope="col">Início</th>
        <th scope="col">Fim</th>
        <th scope="col">Ciclos avaliativos</th>
        <th scope="col"><span class="sr-only">Ações</span></th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="periodo in periodos" :key="periodo.id">
        <td>{{ periodo.nome }}</td>
        <td>{{ REGIMES[periodo.regime] }}</td>
        <td>{{ formatarData(periodo.data_inicio) }}</td>
        <td>{{ formatarData(periodo.data_fim) }}</td>
        <td>
          <div v-for="ciclo in periodo.ciclos" :key="ciclo.id" class="text-down-01">
            {{ ciclo.nome }}: {{ formatarData(ciclo.data_inicio) }} a
            {{ formatarData(ciclo.data_fim) }}
          </div>
        </td>
        <td class="text-right text-nowrap">
          <BrButton
            circular
            icone="fas fa-pen"
            :rotulo="`Editar ${periodo.nome}`"
            @click="editar(periodo)"
          />
          <BrButton
            circular
            icone="fas fa-trash"
            :rotulo="`Excluir ${periodo.nome}`"
            @click="excluindo = periodo"
          />
        </td>
      </tr>
    </tbody>
  </BrTable>

  <BrModal
    v-if="formulario"
    :titulo="editandoId === null ? 'Novo período letivo' : 'Editar período letivo'"
    tamanho="large"
    @fechar="formulario = null"
  >
    <form id="form-periodo" class="formulario" @submit.prevent="salvar">
      <div class="linha">
        <BrSelect
          :model-value="formulario.regime"
          rotulo="Regime"
          :opcoes="opcoesRegime"
          @update:model-value="trocarRegime"
        />
        <BrInput
          v-model="formulario.ano"
          rotulo="Ano"
          type="number"
          min="2000"
          max="2100"
          required
          @change="atualizarNomeSemestral"
        />
        <BrSelect
          v-if="formulario.regime === 'SEMESTRAL'"
          v-model="formulario.semestre"
          rotulo="Semestre"
          :opcoes="opcoesSemestre"
          @update:model-value="atualizarNomeSemestral"
        />
        <BrInput v-model="formulario.nome" rotulo="Nome" required />
      </div>
      <div class="linha">
        <BrInput v-model="formulario.data_inicio" rotulo="Início" type="date" required />
        <BrInput v-model="formulario.data_fim" rotulo="Fim" type="date" required />
      </div>

      <fieldset>
        <legend>
          {{ formulario.regime === 'ANUAL' ? 'Trimestres' : 'Ciclos avaliativos' }}
        </legend>
        <div v-for="(ciclo, i) in formulario.ciclos" :key="i" class="linha ciclo">
          <BrInput
            v-model="ciclo.nome"
            :rotulo="`Nome do ciclo ${i + 1}`"
            :placeholder="formulario.regime === 'ANUAL' ? `${i + 1}º trimestre` : `${i + 1}º ciclo`"
          />
          <BrInput
            v-model="ciclo.data_inicio"
            :rotulo="`Início do ciclo ${i + 1}`"
            type="date"
            required
          />
          <BrInput
            v-model="ciclo.data_fim"
            :rotulo="`Fim do ciclo ${i + 1}`"
            type="date"
            required
          />
          <BrButton
            circular
            icone="fas fa-times"
            :rotulo="`Remover ciclo ${i + 1}`"
            :disabled="formulario.ciclos.length === 1"
            class="remover"
            @click="formulario.ciclos.splice(i, 1)"
          />
        </div>
        <BrButton
          icone="fas fa-plus"
          densidade="small"
          :disabled="formulario.ciclos.length >= 6"
          @click="formulario.ciclos.push(cicloVazio())"
        >
          Adicionar ciclo
        </BrButton>
      </fieldset>

      <BrMessage v-if="erroForm" estado="danger">{{ erroForm }}</BrMessage>
    </form>
    <template #rodape>
      <BrButton variante="secondary" @click="formulario = null">Cancelar</BrButton>
      <BrButton type="submit" form="form-periodo" variante="primary" :carregando="salvando">
        Salvar
      </BrButton>
    </template>
  </BrModal>

  <ModalConfirmacao
    v-if="excluindo"
    titulo="Excluir período letivo"
    :acao="excluir"
    @fechar="excluindo = null"
  >
    Excluir o período <strong>{{ excluindo.nome }}</strong
    >?
  </ModalConfirmacao>
</template>

<style scoped>
.ciclo {
  margin-bottom: var(--spacing-scale-2x);
}

.ciclo .remover {
  flex: 0 0 auto;
}
</style>
