<script setup lang="ts">
// Mensagem do GovBR-DS: https://www.gov.br/ds/components/message
import BrButton from './BrButton.vue'

type Estado = 'danger' | 'success' | 'warning' | 'info'

defineProps<{
  estado: Estado
  titulo?: string
  fechavel?: boolean
}>()

defineEmits<{ fechar: [] }>()

const icones: Record<Estado, string> = {
  danger: 'fas fa-times-circle fa-lg',
  success: 'fas fa-check-circle fa-lg',
  warning: 'fas fa-exclamation-triangle fa-lg',
  info: 'fas fa-info-circle fa-lg',
}
</script>

<template>
  <div class="br-message" :class="estado">
    <div class="icon"><i :class="icones[estado]" aria-hidden="true"></i></div>
    <div class="content" role="alert">
      <span v-if="titulo" class="message-title">{{ titulo }}</span>
      <span class="message-body"> <slot /></span>
    </div>
    <div v-if="fechavel" class="close">
      <BrButton
        circular
        densidade="small"
        icone="fas fa-times"
        rotulo="Fechar a mensagem"
        @click="$emit('fechar')"
      />
    </div>
  </div>
</template>
