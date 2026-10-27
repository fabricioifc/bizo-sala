<script setup lang="ts">
// Cabeçalho compacto do GovBR-DS: https://www.gov.br/ds/components/header
// No modo compacto o DS oculta a assinatura; o título fica em header-bottom.
defineProps<{
  titulo: string
  subtitulo?: string
  logo?: string
}>()
</script>

<template>
  <header class="br-header compact">
    <div class="container-lg">
      <div class="header-top">
        <div class="header-logo">
          <img v-if="logo" :src="logo" alt="" width="32" height="32" />
        </div>
        <div class="header-actions">
          <slot name="acoes" />
        </div>
      </div>
      <div class="header-bottom">
        <div class="header-menu">
          <div class="header-info">
            <div class="header-title">{{ titulo }}</div>
            <div v-if="subtitulo" class="header-subtitle">{{ subtitulo }}</div>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>
