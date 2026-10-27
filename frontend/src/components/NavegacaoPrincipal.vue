<script setup lang="ts">
import { useRoute } from 'vue-router'

const route = useRoute()

const links = [
  { para: '/', rotulo: 'Painel', icone: 'fas fa-home' },
  { para: '/turmas', rotulo: 'Turmas', icone: 'fas fa-users' },
  { para: '/cursos', rotulo: 'Cursos', icone: 'fas fa-graduation-cap' },
  { para: '/periodos', rotulo: 'Períodos', icone: 'fas fa-calendar-alt' },
  { para: '/dias-nao-letivos', rotulo: 'Dias não letivos', icone: 'fas fa-calendar-times' },
]

/** Ativo também nas subpáginas (ex.: /turmas/1/estudantes), que não são rotas aninhadas */
function ativo(para: string): boolean {
  return para === '/' ? route.path === '/' : route.path.startsWith(para)
}
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
</style>
