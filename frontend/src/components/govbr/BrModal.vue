<script setup lang="ts">
// Modal do GovBR-DS com scrim de foco: https://www.gov.br/ds/components/modal
import { nextTick, onBeforeUnmount, onMounted, ref, useId } from 'vue'

import BrButton from './BrButton.vue'

withDefaults(defineProps<{ titulo: string; tamanho?: 'small' | 'medium' | 'large' }>(), {
  tamanho: 'medium',
})
const emit = defineEmits<{ fechar: [] }>()

const idTitulo = useId()
const modal = ref<HTMLElement>()
let focoAnterior: HTMLElement | null = null

const FOCAVEIS =
  'a[href], button:not([disabled]), input:not([disabled]):not([tabindex="-1"]), select, textarea, [tabindex]:not([tabindex="-1"])'

function teclado(evento: KeyboardEvent) {
  if (evento.key === 'Escape') {
    evento.preventDefault()
    emit('fechar')
    return
  }
  // Mantém o foco dentro do modal
  if (evento.key !== 'Tab' || !modal.value) return
  const focaveis = [...modal.value.querySelectorAll<HTMLElement>(FOCAVEIS)]
  const primeiro = focaveis[0]
  const ultimo = focaveis[focaveis.length - 1]
  if (!primeiro || !ultimo) return
  if (evento.shiftKey && document.activeElement === primeiro) {
    evento.preventDefault()
    ultimo.focus()
  } else if (!evento.shiftKey && document.activeElement === ultimo) {
    evento.preventDefault()
    primeiro.focus()
  }
}

onMounted(async () => {
  focoAnterior = document.activeElement as HTMLElement | null
  document.body.style.overflow = 'hidden'
  await nextTick()
  const corpo = modal.value?.querySelector<HTMLElement>('.br-modal-body')
  ;(corpo?.querySelector<HTMLElement>(FOCAVEIS) ?? modal.value)?.focus()
})

onBeforeUnmount(() => {
  document.body.style.overflow = ''
  focoAnterior?.focus()
})
</script>

<template>
  <Teleport to="body">
    <div class="br-scrim foco active" @keydown="teclado">
      <div
        ref="modal"
        class="br-modal"
        :class="tamanho"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="idTitulo"
        tabindex="-1"
      >
        <div class="br-modal-header">
          <div :id="idTitulo" class="modal-title">{{ titulo }}</div>
          <BrButton
            class="close"
            circular
            icone="fas fa-times"
            rotulo="Fechar"
            @click="emit('fechar')"
          />
        </div>
        <div class="br-modal-body">
          <slot />
        </div>
        <div v-if="$slots.rodape" class="br-modal-footer justify-content-end">
          <slot name="rodape" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.br-modal {
  max-height: 90vh;
  overflow-y: auto;
  width: min(100% - 2 * var(--spacing-scale-2x), var(--largura-modal, 600px));
}

.br-modal.large {
  --largura-modal: 860px;
}

.br-modal.small {
  --largura-modal: 420px;
}

.br-modal-footer {
  gap: var(--spacing-scale-2x);
}
</style>
