<script setup lang="ts">
// Checkbox do GovBR-DS: https://www.gov.br/ds/components/checkbox
import { useId } from 'vue'

defineProps<{ rotulo: string; disabled?: boolean }>()

const marcado = defineModel<boolean>({ default: false })
const id = useId()
</script>

<template>
  <div class="br-checkbox">
    <input :id="id" v-model="marcado" type="checkbox" :disabled="disabled" />
    <label :for="id">{{ rotulo }}</label>
  </div>
</template>
