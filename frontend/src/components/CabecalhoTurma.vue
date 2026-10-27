<script setup lang="ts">
import type { Turma } from '@/api/client'
import { DIAS_SEMANA } from '@/utils/formato'

defineProps<{ turma: Turma; aba: 'estudantes' | 'aulas' | 'conteudo' | 'notas' }>()

const abas = [
  { id: 'aulas', rotulo: 'Aulas e chamada', icone: 'fas fa-calendar-check' },
  { id: 'notas', rotulo: 'Notas', icone: 'fas fa-clipboard-list' },
  { id: 'conteudo', rotulo: 'Conteúdo', icone: 'fas fa-book-open' },
  { id: 'estudantes', rotulo: 'Estudantes', icone: 'fas fa-user-graduate' },
] as const
</script>

<template>
  <nav class="br-breadcrumb" aria-label="Breadcrumbs">
    <ol class="crumb-list">
      <li class="crumb"><RouterLink to="/turmas">Turmas</RouterLink></li>
      <li class="crumb" data-active="active">
        <i class="icon fas fa-chevron-right" aria-hidden="true"></i>
        <span>{{ turma.disciplina }} – {{ turma.nome }}</span>
      </li>
    </ol>
  </nav>

  <h1 class="mb-1">{{ turma.disciplina }} – {{ turma.nome }}</h1>
  <p class="text-down-01">
    {{ turma.curso_nome }} · {{ turma.periodo_nome }} · {{ turma.carga_horaria_horas }} h ({{
      turma.horas_aula_previstas
    }}
    horas-aula) ·
    {{ turma.horarios.map((h) => `${DIAS_SEMANA[h.dia_semana]} (${h.aulas})`).join(', ') }}
  </p>

  <div class="br-tab mb-3">
    <nav class="tab-nav" aria-label="Seções da turma">
      <ul>
        <li v-for="a in abas" :key="a.id" class="tab-item" :class="{ active: a.id === aba }">
          <RouterLink
            :to="`/turmas/${turma.id}/${a.id}`"
            :aria-current="a.id === aba ? 'page' : undefined"
          >
            <span class="name"><i :class="a.icone" aria-hidden="true"></i> {{ a.rotulo }}</span>
          </RouterLink>
        </li>
      </ul>
    </nav>
  </div>
</template>

<style scoped>
/* O DS só estiliza a aba ativa quando é <button>; aqui as abas são links de rota */
.br-tab .tab-item.active a {
  border-bottom: 4px solid var(--active);
  color: var(--active);
}
</style>
