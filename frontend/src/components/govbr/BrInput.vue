<script setup lang="ts">
// Campo de texto do GovBR-DS: https://www.gov.br/ds/components/input
import { computed, ref, useId } from 'vue'

import BrButton from './BrButton.vue'

type Estado = 'danger' | 'success' | 'warning' | 'info'

const props = withDefaults(
  defineProps<{
    rotulo: string
    type?: string
    placeholder?: string
    autocomplete?: string
    required?: boolean
    disabled?: boolean
    densidade?: 'small' | 'medium' | 'large'
    estado?: Estado
    /** Mensagem exibida abaixo do campo (erro, sucesso, aviso ou informação) */
    mensagem?: string
  }>(),
  { type: 'text', densidade: 'medium' },
)

const valor = defineModel<string>({ default: '' })

const id = useId()
const idMensagem = `${id}-mensagem`
const senhaVisivel = ref(false)

const ehSenha = computed(() => props.type === 'password')
const tipoEfetivo = computed(() => (ehSenha.value && senhaVisivel.value ? 'text' : props.type))

const iconesEstado: Record<Estado, string> = {
  danger: 'fas fa-times-circle',
  success: 'fas fa-check-circle',
  warning: 'fas fa-exclamation-triangle',
  info: 'fas fa-info-circle',
}
</script>

<template>
  <div
    class="br-input"
    :class="[estado, densidade !== 'medium' && densidade, { 'input-button': ehSenha }]"
  >
    <label :for="id">{{ rotulo }}</label>
    <input
      :id="id"
      v-model="valor"
      :type="tipoEfetivo"
      :placeholder="placeholder"
      :autocomplete="autocomplete"
      :required="required"
      :disabled="disabled"
      :aria-invalid="estado === 'danger' || undefined"
      :aria-describedby="mensagem ? idMensagem : undefined"
    />
    <BrButton
      v-if="ehSenha"
      :icone="senhaVisivel ? 'fas fa-eye-slash' : 'fas fa-eye'"
      :rotulo="senhaVisivel ? 'Ocultar senha' : 'Exibir senha'"
      role="switch"
      :aria-checked="senhaVisivel"
      @click="senhaVisivel = !senhaVisivel"
    />
    <span v-if="mensagem" :id="idMensagem" class="feedback" :class="estado ?? 'info'" role="alert">
      <i :class="iconesEstado[estado ?? 'info']" aria-hidden="true"></i>{{ mensagem }}
    </span>
  </div>
</template>
