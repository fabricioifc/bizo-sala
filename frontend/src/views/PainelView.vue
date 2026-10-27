<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { api, exigir, type AulaDoDia, type Turma } from '@/api/client'
import { BrCard, BrMessage } from '@/components/govbr'
import { prepararOffline } from '@/offline/chamadas'
import { useAlertasStore } from '@/stores/alertas'
import { useAuthStore } from '@/stores/auth'
import { DIAS_SEMANA, formatarDataCurta, hojeIso } from '@/utils/formato'

const auth = useAuthStore()
const alertas = useAlertasStore()
const turmas = ref<Turma[] | null>(null)
const aulasHoje = ref<AulaDoDia[]>([])
const erro = ref('')
const hoje = hojeIso()

onMounted(async () => {
  try {
    ;[turmas.value, aulasHoje.value] = await Promise.all([
      exigir(api.GET('/api/turmas')),
      exigir(api.GET('/api/aulas', { params: { query: { data: hoje } } })),
    ])
    // Deixa as chamadas de hoje guardadas no aparelho, caso a internet da sala caia
    void prepararOffline(aulasHoje.value.filter((a) => a.status !== 'CANCELADA').map((a) => a.id))
  } catch (e) {
    erro.value = (e as Error).message
  }
})
</script>

<template>
  <h1>Olá, {{ auth.usuario?.nome }}</h1>
  <BrMessage v-if="erro" estado="danger">{{ erro }}</BrMessage>
  <BrMessage v-if="alertas.pendentes" estado="warning" titulo="Avisar o SISAE.">
    {{ alertas.pendentes }} estudante(s) atingiram o limite de faltas.
    <RouterLink to="/alertas">Ver alertas</RouterLink>
  </BrMessage>

  <section v-if="aulasHoje.length" class="mb-4" aria-labelledby="titulo-hoje">
    <h2 id="titulo-hoje">Aulas de hoje · {{ formatarDataCurta(hoje) }}</h2>
    <div class="cartoes">
      <BrCard v-for="aula in aulasHoje" :key="aula.id">
        <p class="mb-1">
          <strong>{{ aula.disciplina }} – {{ aula.turma_nome }}</strong>
        </p>
        <p class="text-down-01 mb-2">
          {{ aula.horas_aula }} hora(s)-aula ·
          {{
            aula.status === 'DADA'
              ? 'chamada feita'
              : aula.status === 'CANCELADA'
                ? `cancelada (${aula.motivo_cancelamento})`
                : 'chamada pendente'
          }}
        </p>
        <RouterLink
          v-if="aula.status !== 'CANCELADA'"
          :to="`/aulas/${aula.id}/chamada`"
          class="br-button block"
          :class="aula.status === 'DADA' ? 'secondary' : 'primary'"
        >
          <i class="fas fa-clipboard-check" aria-hidden="true"></i>
          {{ aula.status === 'DADA' ? 'Ver chamada' : 'Fazer chamada' }}
        </RouterLink>
      </BrCard>
    </div>
  </section>

  <BrMessage v-if="turmas?.length === 0" estado="info" titulo="Nenhuma turma cadastrada.">
    Comece cadastrando um <RouterLink to="/cursos">curso</RouterLink>, um
    <RouterLink to="/periodos">período letivo</RouterLink> e depois as
    <RouterLink to="/turmas">turmas</RouterLink>.
  </BrMessage>

  <section v-else-if="turmas" aria-labelledby="titulo-turmas">
    <h2 id="titulo-turmas">Turmas</h2>
    <div class="cartoes">
      <BrCard v-for="turma in turmas" :key="turma.id">
        <template #cabecalho>
          <RouterLink :to="`/turmas/${turma.id}/aulas`" class="titulo">
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
  </section>
</template>

<style scoped>
.cartoes {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--spacing-scale-2x);
}

.titulo {
  font-weight: var(--font-weight-semi-bold);
}
</style>
