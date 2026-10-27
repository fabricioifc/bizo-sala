<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { api, exigir, type Curso, type Periodo, type Turma } from '@/api/client'
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
import { DIAS_SEMANA, NIVEIS } from '@/utils/formato'

interface Formulario {
  disciplina: string
  nome: string
  curso_id: number | null
  periodo_id: number | null
  carga_horaria_horas: number | ''
  // Segunda a sábado: dia marcado e quantas horas-aula
  dias: { marcado: boolean; aulas: number | '' }[]
}

const turmas = ref<Turma[]>([])
const cursos = ref<Curso[]>([])
const periodos = ref<Periodo[]>([])
const erroCarga = ref('')

const formulario = ref<Formulario | null>(null)
const editandoId = ref<number | null>(null)
const salvando = ref(false)
const erroForm = ref('')
const excluindo = ref<Turma | null>(null)

const DIAS_COM_AULA = DIAS_SEMANA.slice(0, 6)

const opcoesCurso = computed<Opcao<number>[]>(() =>
  cursos.value.map((c) => ({ valor: c.id, rotulo: c.nome })),
)

/** Só períodos com o mesmo regime do curso escolhido (anual × semestral) */
const opcoesPeriodo = computed<Opcao<number>[]>(() => {
  const curso = cursos.value.find((c) => c.id === formulario.value?.curso_id)
  return periodos.value
    .filter((p) => !curso || p.regime === curso.regime)
    .map((p) => ({ valor: p.id, rotulo: p.nome }))
})

const resumo = computed(() => {
  const f = formulario.value
  if (!f || !f.carga_horaria_horas) return null
  const horasAula = Math.ceil((Number(f.carga_horaria_horas) * 60) / 50)
  const porSemana = f.dias.reduce((s, d) => s + (d.marcado ? Number(d.aulas) || 0 : 0), 0)
  return { horasAula, porSemana, semanas: porSemana ? Math.ceil(horasAula / porSemana) : null }
})

async function carregar() {
  try {
    ;[turmas.value, cursos.value, periodos.value] = await Promise.all([
      exigir(api.GET('/api/turmas')),
      exigir(api.GET('/api/cursos')),
      exigir(api.GET('/api/periodos')),
    ])
  } catch (e) {
    erroCarga.value = (e as Error).message
  }
}

function novo() {
  editandoId.value = null
  erroForm.value = ''
  formulario.value = {
    disciplina: '',
    nome: '',
    curso_id: cursos.value.length === 1 ? cursos.value[0]!.id : null,
    periodo_id: null,
    carga_horaria_horas: 60,
    dias: DIAS_COM_AULA.map(() => ({ marcado: false, aulas: 2 })),
  }
}

function editar(turma: Turma) {
  editandoId.value = turma.id
  erroForm.value = ''
  formulario.value = {
    disciplina: turma.disciplina,
    nome: turma.nome,
    curso_id: turma.curso_id,
    periodo_id: turma.periodo_id,
    carga_horaria_horas: turma.carga_horaria_horas,
    dias: DIAS_COM_AULA.map((_, i) => {
      const horario = turma.horarios.find((h) => h.dia_semana === i)
      return { marcado: !!horario, aulas: horario?.aulas ?? 2 }
    }),
  }
}

function trocarCurso(cursoId: number | null) {
  if (!formulario.value) return
  formulario.value.curso_id = cursoId
  const periodoValido = opcoesPeriodo.value.some((p) => p.valor === formulario.value?.periodo_id)
  if (!periodoValido) formulario.value.periodo_id = null
}

async function salvar() {
  const f = formulario.value
  if (!f) return
  erroForm.value = ''
  if (!f.curso_id || !f.periodo_id) {
    erroForm.value = 'Selecione o curso e o período letivo'
    return
  }
  const horarios = f.dias
    .map((d, dia_semana) => ({ dia_semana, aulas: Number(d.aulas), marcado: d.marcado }))
    .filter((d) => d.marcado)
    .map(({ dia_semana, aulas }) => ({ dia_semana, aulas }))
  if (horarios.length === 0) {
    erroForm.value = 'Marque ao menos um dia de aula'
    return
  }
  const body = {
    disciplina: f.disciplina,
    nome: f.nome,
    curso_id: f.curso_id,
    periodo_id: f.periodo_id,
    carga_horaria_horas: Number(f.carga_horaria_horas),
    horarios,
  }
  salvando.value = true
  try {
    if (editandoId.value === null) {
      await exigir(api.POST('/api/turmas', { body }))
    } else {
      const params = { path: { turma_id: editandoId.value } }
      await exigir(api.PUT('/api/turmas/{turma_id}', { params, body }))
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
  const params = { path: { turma_id: excluindo.value.id } }
  await exigir(api.DELETE('/api/turmas/{turma_id}', { params }))
  await carregar()
}

onMounted(carregar)
</script>

<template>
  <h1>Turmas</h1>
  <BrMessage v-if="erroCarga" estado="danger">{{ erroCarga }}</BrMessage>
  <BrMessage v-else-if="cursos.length === 0 || periodos.length === 0" estado="info">
    Antes de criar turmas, cadastre ao menos um
    <RouterLink to="/cursos">curso</RouterLink> e um
    <RouterLink to="/periodos">período letivo</RouterLink>.
  </BrMessage>

  <BrTable titulo="Turmas cadastradas" :vazia="turmas.length === 0">
    <template #acoes>
      <BrButton
        variante="primary"
        icone="fas fa-plus"
        :disabled="cursos.length === 0 || periodos.length === 0"
        @click="novo"
      >
        Nova turma
      </BrButton>
    </template>
    <thead>
      <tr>
        <th scope="col">Disciplina</th>
        <th scope="col">Turma</th>
        <th scope="col">Curso</th>
        <th scope="col">Período</th>
        <th scope="col">Carga horária</th>
        <th scope="col">Horários</th>
        <th scope="col">Estudantes</th>
        <th scope="col"><span class="sr-only">Ações</span></th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="turma in turmas" :key="turma.id">
        <td>
          <RouterLink :to="`/turmas/${turma.id}/aulas`">{{ turma.disciplina }}</RouterLink>
        </td>
        <td>{{ turma.nome }}</td>
        <td>
          {{ turma.curso_nome }}
          <div class="text-down-01">{{ NIVEIS[turma.nivel] }}</div>
        </td>
        <td>{{ turma.periodo_nome }}</td>
        <td>
          {{ turma.carga_horaria_horas }} h
          <div class="text-down-01">{{ turma.horas_aula_previstas }} horas-aula</div>
        </td>
        <td>
          <div v-for="h in turma.horarios" :key="h.dia_semana" class="text-down-01">
            {{ DIAS_SEMANA[h.dia_semana] }}: {{ h.aulas }}
            {{ h.aulas === 1 ? 'aula' : 'aulas' }}
          </div>
        </td>
        <td>{{ turma.total_estudantes }}</td>
        <td class="text-right text-nowrap">
          <BrButton
            circular
            icone="fas fa-user-graduate"
            :rotulo="`Estudantes de ${turma.disciplina} ${turma.nome}`"
            @click="$router.push(`/turmas/${turma.id}/estudantes`)"
          />
          <BrButton
            circular
            icone="fas fa-pen"
            :rotulo="`Editar ${turma.disciplina} ${turma.nome}`"
            @click="editar(turma)"
          />
          <BrButton
            circular
            icone="fas fa-trash"
            :rotulo="`Excluir ${turma.disciplina} ${turma.nome}`"
            @click="excluindo = turma"
          />
        </td>
      </tr>
    </tbody>
  </BrTable>

  <BrModal
    v-if="formulario"
    :titulo="editandoId === null ? 'Nova turma' : 'Editar turma'"
    tamanho="large"
    @fechar="formulario = null"
  >
    <form id="form-turma" class="formulario" @submit.prevent="salvar">
      <div class="linha">
        <BrInput
          v-model="formulario.disciplina"
          rotulo="Disciplina"
          placeholder="Ex.: Programação I"
          required
        />
        <BrInput v-model="formulario.nome" rotulo="Turma" placeholder="Ex.: 1º INFO" required />
      </div>
      <div class="linha">
        <BrSelect
          :model-value="formulario.curso_id"
          rotulo="Curso"
          :opcoes="opcoesCurso"
          @update:model-value="trocarCurso"
        />
        <BrSelect
          v-model="formulario.periodo_id"
          rotulo="Período letivo"
          :opcoes="opcoesPeriodo"
          :mensagem="opcoesPeriodo.length === 0 ? 'Nenhum período com o regime deste curso' : ''"
          :estado="opcoesPeriodo.length === 0 ? 'warning' : undefined"
        />
        <BrInput
          v-model="formulario.carga_horaria_horas"
          rotulo="Carga horária (horas)"
          type="number"
          min="1"
          max="1000"
          required
        />
      </div>

      <fieldset>
        <legend>Dias de aula e horas-aula (50 min) em cada dia</legend>
        <div class="dias">
          <div v-for="(dia, i) in formulario.dias" :key="i" class="dia">
            <BrCheckbox v-model="dia.marcado" :rotulo="DIAS_COM_AULA[i]!" />
            <BrInput
              v-if="dia.marcado"
              v-model="dia.aulas"
              :rotulo="`Aulas na ${DIAS_COM_AULA[i]!.toLowerCase()}`"
              type="number"
              min="1"
              max="8"
              densidade="small"
              required
            />
          </div>
        </div>
      </fieldset>

      <BrMessage v-if="resumo" estado="info" titulo="Previsão.">
        {{ resumo.horasAula }} horas-aula para cumprir {{ formulario.carga_horaria_horas }} h
        <template v-if="resumo.semanas">
          · {{ resumo.porSemana }} por semana ≈ {{ resumo.semanas }} semanas de aula
        </template>
      </BrMessage>
      <BrMessage v-if="erroForm" estado="danger">{{ erroForm }}</BrMessage>
    </form>
    <template #rodape>
      <BrButton variante="secondary" @click="formulario = null">Cancelar</BrButton>
      <BrButton type="submit" form="form-turma" variante="primary" :carregando="salvando">
        Salvar
      </BrButton>
    </template>
  </BrModal>

  <ModalConfirmacao
    v-if="excluindo"
    titulo="Excluir turma"
    :acao="excluir"
    @fechar="excluindo = null"
  >
    Excluir a turma <strong>{{ excluindo.disciplina }} – {{ excluindo.nome }}</strong
    >? As matrículas dos estudantes nesta turma também serão removidas.
  </ModalConfirmacao>
</template>

<style scoped>
.dias {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--spacing-scale-2x);
}

.dia {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-scale-base);
}
</style>
