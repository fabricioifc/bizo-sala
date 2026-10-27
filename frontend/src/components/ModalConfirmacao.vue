<script setup lang="ts">
import { ref } from 'vue'

import { BrButton, BrMessage, BrModal } from '@/components/govbr'

const props = withDefaults(
  defineProps<{
    titulo: string
    rotuloConfirmar?: string
    /** Ação executada ao confirmar; erros lançados são exibidos no modal */
    acao: () => Promise<void>
  }>(),
  { rotuloConfirmar: 'Excluir' },
)
const emit = defineEmits<{ fechar: [] }>()

const executando = ref(false)
const erro = ref('')

async function confirmar() {
  executando.value = true
  erro.value = ''
  try {
    await props.acao()
    emit('fechar')
  } catch (e) {
    erro.value = e instanceof Error ? e.message : 'Não foi possível concluir'
  } finally {
    executando.value = false
  }
}
</script>

<template>
  <BrModal :titulo="titulo" tamanho="small" @fechar="emit('fechar')">
    <slot />
    <BrMessage v-if="erro" class="mt-3" estado="danger">{{ erro }}</BrMessage>
    <template #rodape>
      <BrButton variante="secondary" @click="emit('fechar')">Cancelar</BrButton>
      <BrButton variante="primary" :carregando="executando" @click="confirmar">
        {{ rotuloConfirmar }}
      </BrButton>
    </template>
  </BrModal>
</template>
