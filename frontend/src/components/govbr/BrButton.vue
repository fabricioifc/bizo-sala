<script setup lang="ts">
// Botão do GovBR-DS: https://www.gov.br/ds/components/button
withDefaults(
  defineProps<{
    /** Ênfase: primário, secundário ou terciário (padrão do DS, sem classe) */
    variante?: 'primary' | 'secondary' | 'tertiary'
    type?: 'button' | 'submit' | 'reset'
    icone?: string
    /** Botão só com ícone (circular); exige `rotulo` para acessibilidade */
    circular?: boolean
    rotulo?: string
    bloco?: boolean
    densidade?: 'small' | 'medium' | 'large'
    carregando?: boolean
    disabled?: boolean
  }>(),
  { variante: 'tertiary', type: 'button', densidade: 'medium' },
)
</script>

<template>
  <button
    class="br-button"
    :class="[
      variante !== 'tertiary' && variante,
      densidade !== 'medium' && densidade,
      { circle: circular, block: bloco, loading: carregando },
    ]"
    :type="type"
    :disabled="disabled || carregando"
    :aria-label="rotulo"
    :aria-busy="carregando || undefined"
  >
    <i v-if="icone" :class="icone" aria-hidden="true"></i>
    <slot />
  </button>
</template>
