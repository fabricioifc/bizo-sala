<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api, exigir, type Turma } from '@/api/client'
import { BrCard, BrMessage } from '@/components/govbr'
import { useAuthStore } from '@/stores/auth'
import { DIAS_SEMANA } from '@/utils/formato'

const auth = useAuthStore()
const turmas = ref<Turma[] | null>(null)
const erro = ref('')

onMounted(async () => {
  try {
    turmas.value = await exigir(api.GET('/api/turmas'))
  } catch (e) {
    erro.value = (e as Error).message
  }
})
</script>

<template>
  <h1>Olá, {{ auth.usuario?.nome }}</h1>
  <BrMessage v-if="erro" estado="danger">{{ erro }}</BrMessage>

  <BrMessage v-else-if="turmas?.length === 0" estado="info" titulo="Nenhuma turma cadastrada.">
    Comece cadastrando um <RouterLink to="/cursos">curso</RouterLink>, um
    <RouterLink to="/periodos">período letivo</RouterLink> e depois as
    <RouterLink to="/turmas">turmas</RouterLink>.
  </BrMessage>

  <div v-else class="turmas">
    <BrCard v-for="turma in turmas" :key="turma.id">
      <template #cabecalho>
        <RouterLink :to="`/turmas/${turma.id}/estudantes`" class="titulo">
          {{ turma.disciplina }} – {{ turma.nome }}
        </RouterLink>
      </template>
      <p class="text-down-01 mb-1">{{ turma.curso_nome }} · {{ turma.periodo_nome }}</p>
      <p class="mb-0">
        <i class="fas fa-users" aria-hidden="true"></i> {{ turma.total_estudantes }} estudantes ·
        <i class="fas fa-clock" aria-hidden="true"></i> {{ turma.carga_horaria_horas }} h
      </p>
      <p class="text-down-01 mb-0">
        {{ turma.horarios.map((h) => DIAS_SEMANA[h.dia_semana]).join(', ') }}
      </p>
    </BrCard>
  </div>
</template>

<style scoped>
.turmas {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--spacing-scale-2x);
}

.titulo {
  font-weight: var(--font-weight-semi-bold);
}
</style>
