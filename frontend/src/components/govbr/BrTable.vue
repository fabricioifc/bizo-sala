<script setup lang="ts">
// Tabela do GovBR-DS: https://www.gov.br/ds/components/table
defineProps<{ titulo: string; vazia?: boolean; mensagemVazia?: string }>()
</script>

<template>
  <div class="br-table">
    <div class="table-header">
      <div class="top-bar">
        <div class="table-title">{{ titulo }}</div>
        <div class="acoes">
          <slot name="acoes" />
        </div>
      </div>
    </div>
    <div class="rolagem">
      <table>
        <caption class="sr-only">
          {{
            titulo
          }}
        </caption>
        <slot />
      </table>
    </div>
    <p v-if="vazia" class="vazia">{{ mensagemVazia ?? 'Nenhum registro.' }}</p>
  </div>
</template>

<style scoped>
.top-bar {
  flex-wrap: wrap;
  gap: var(--spacing-scale-2x);
}

.acoes {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-scale-base);
  margin-left: auto;
}

.rolagem {
  overflow-x: auto;
}

.vazia {
  padding: var(--spacing-scale-3x);
  color: var(--gray-60);
  text-align: center;
}
</style>
