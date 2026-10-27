<script setup lang="ts">
// Área de texto do GovBR-DS: https://www.gov.br/ds/components/textarea
import { useId } from 'vue'

withDefaults(
  defineProps<{
    rotulo: string
    placeholder?: string
    linhas?: number
    maxlength?: number
    /** Esconde o rótulo visualmente (continua acessível ao leitor de tela) */
    rotuloOculto?: boolean
  }>(),
  { linhas: 2 },
)

const texto = defineModel<string>({ default: '' })
const id = useId()
</script>

<template>
  <div class="br-textarea">
    <label :for="id" :class="{ 'sr-only': rotuloOculto }">{{ rotulo }}</label>
    <textarea
      :id="id"
      v-model="texto"
      :rows="linhas"
      :placeholder="placeholder"
      :maxlength="maxlength"
    ></textarea>
  </div>
</template>
