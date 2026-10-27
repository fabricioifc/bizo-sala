<script setup lang="ts" generic="V extends string | number">
// Select (seleção simples) do GovBR-DS: https://www.gov.br/ds/components/select
// Comportamento implementado em Vue (sem o JS do core), seguindo o padrão combobox da WAI-ARIA.
import { computed, ref, useId } from 'vue'

import type { Estado, Opcao } from './tipos'

const props = withDefaults(
  defineProps<{
    rotulo: string
    opcoes: Opcao<V>[]
    placeholder?: string
    disabled?: boolean
    estado?: Estado
    mensagem?: string
  }>(),
  { placeholder: 'Selecione' },
)

const valor = defineModel<V | null>({ default: null })

const id = useId()
const idLista = `${id}-lista`
const idMensagem = `${id}-mensagem`
const aberto = ref(false)
const destaque = ref(-1)

const rotuloSelecionado = computed(
  () => props.opcoes.find((o) => o.valor === valor.value)?.rotulo ?? '',
)

function abrir() {
  if (props.disabled) return
  aberto.value = true
  destaque.value = Math.max(
    0,
    props.opcoes.findIndex((o) => o.valor === valor.value),
  )
}

function fechar() {
  aberto.value = false
  destaque.value = -1
}

function selecionar(opcao: Opcao<V>) {
  valor.value = opcao.valor
  fechar()
}

function teclado(evento: KeyboardEvent) {
  const total = props.opcoes.length
  switch (evento.key) {
    case 'ArrowDown':
    case 'ArrowUp':
      evento.preventDefault()
      if (!aberto.value) return abrir()
      destaque.value = (destaque.value + (evento.key === 'ArrowDown' ? 1 : -1) + total) % total
      break
    case 'Enter':
    case ' ':
      evento.preventDefault()
      if (!aberto.value) return abrir()
      if (props.opcoes[destaque.value]) selecionar(props.opcoes[destaque.value])
      break
    case 'Escape':
      if (aberto.value) {
        evento.preventDefault()
        fechar()
      }
      break
  }
}
</script>

<template>
  <div class="br-select" @focusout="fechar">
    <div class="br-input" :class="estado">
      <label :for="id">{{ rotulo }}</label>
      <input
        :id="id"
        type="text"
        readonly
        role="combobox"
        :value="rotuloSelecionado"
        :placeholder="placeholder"
        :disabled="disabled"
        :aria-expanded="aberto"
        :aria-controls="idLista"
        :aria-activedescendant="aberto && destaque >= 0 ? `${id}-${destaque}` : undefined"
        :aria-invalid="estado === 'danger' || undefined"
        :aria-describedby="mensagem ? idMensagem : undefined"
        @click="aberto ? fechar() : abrir()"
        @keydown="teclado"
      />
      <button
        class="br-button"
        type="button"
        aria-label="Exibir lista"
        tabindex="-1"
        :disabled="disabled"
        @mousedown.prevent
        @click="aberto ? fechar() : abrir()"
      >
        <i :class="aberto ? 'fas fa-angle-up' : 'fas fa-angle-down'" aria-hidden="true"></i>
      </button>
    </div>
    <div :id="idLista" class="br-list" role="listbox" :expanded="aberto ? '' : undefined">
      <div
        v-for="(opcao, i) in opcoes"
        :id="`${id}-${i}`"
        :key="String(opcao.valor)"
        class="br-item"
        :class="{ selected: opcao.valor === valor, highlighted: i === destaque }"
        role="option"
        :aria-selected="opcao.valor === valor"
        @mousedown.prevent="selecionar(opcao)"
      >
        <div class="br-radio">
          <input
            :id="`${id}-${i}-radio`"
            type="radio"
            :name="id"
            :checked="opcao.valor === valor"
            tabindex="-1"
            aria-hidden="true"
          />
          <label :for="`${id}-${i}-radio`">{{ opcao.rotulo }}</label>
        </div>
      </div>
    </div>
    <span v-if="mensagem" :id="idMensagem" class="feedback" :class="estado ?? 'info'" role="alert">
      {{ mensagem }}
    </span>
  </div>
</template>
