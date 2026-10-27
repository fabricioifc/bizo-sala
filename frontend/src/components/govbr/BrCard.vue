<script setup lang="ts">
// Card do GovBR-DS: https://www.gov.br/ds/components/card
</script>

<template>
  <div class="br-card">
    <div v-if="$slots.cabecalho" class="card-header">
      <slot name="cabecalho" />
    </div>
    <div class="card-content">
      <slot />
    </div>
    <div v-if="$slots.rodape" class="card-footer">
      <slot name="rodape" />
    </div>
  </div>
</template>
