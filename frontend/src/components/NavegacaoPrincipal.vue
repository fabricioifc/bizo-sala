<script setup lang="ts">
import { watch } from 'vue'
import { useRoute } from 'vue-router'

import { useAlertasStore } from '@/stores/alertas'

const route = useRoute()
const alertas = useAlertasStore()

const links = [
  { para: '/', rotulo: 'Painel', icone: 'fas fa-home' },
  { para: '/turmas', rotulo: 'Turmas', icone: 'fas fa-users' },
  { para: '/alertas', rotulo: 'Alertas SISAE', icone: 'fas fa-bell' },
  { para: '/cursos', rotulo: 'Cursos', icone: 'fas fa-graduation-cap' },
  { para: '/periodos', rotulo: 'Períodos', icone: 'fas fa-calendar-alt' },
  { para: '/dias-nao-letivos', rotulo: 'Dias não letivos', icone: 'fas fa-calendar-times' },
]

/** Ativo também nas subpáginas (ex.: /turmas/1/estudantes), que não são rotas aninhadas */
function ativo(para: string): boolean {
  return para === '/' ? route.path === '/' : route.path.startsWith(para)
}

// Mantém o contador de alertas atualizado a cada navegação
watch(() => route.path, alertas.atualizar, { immediate: true })
</script>

<template>
  <nav class="navegacao" aria-label="Navegação principal">
    <div class="container-lg">
      <RouterLink
        v-for="link in links"
        :key="link.para"
        :to="link.para"
        class="br-button small"
        :class="{ active: ativo(link.para) }"
        :aria-current="ativo(link.para) ? 'page' : undefined"
        active-class=""
        exact-active-class=""
      >
        <i :class="link.icone" aria-hidden="true"></i>{{ link.rotulo }}
        <span
          v-if="link.para === '/alertas' && alertas.pendentes"
          class="contador"
          :aria-label="`${alertas.pendentes} pendentes`"
        >
          {{ alertas.pendentes }}
        </span>
      </RouterLink>
    </div>
  </nav>
</template>

<style scoped>
.navegacao {
  background: var(--background-light);
  border-bottom: 1px solid var(--border-color);
}

.navegacao .container-lg {
  display: flex;
  gap: var(--spacing-scale-half);
  overflow-x: auto;
  padding-block: var(--spacing-scale-base);
}

.navegacao a {
  flex-shrink: 0;
}

.contador {
  margin-left: var(--spacing-scale-half);
  min-width: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: var(--danger);
  color: var(--pure-0, #fff);
  font-size: var(--font-size-scale-down-02);
  line-height: 20px;
  text-align: center;
}
</style>
