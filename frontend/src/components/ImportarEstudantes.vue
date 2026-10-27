<script setup lang="ts">
import { computed, ref } from 'vue'

import { api, exigir, type ImportacaoResultado } from '@/api/client'
import { BrButton, BrMessage, BrModal } from '@/components/govbr'
import { lerArquivoTexto } from '@/utils/formato'

const props = defineProps<{ turmaId: number; mostrarResponsavel: boolean }>()
const emit = defineEmits<{ fechar: []; importado: [] }>()

const seletor = ref<HTMLInputElement>()
const nomeArquivo = ref('')
const conteudo = ref('')
const previa = ref<ImportacaoResultado | null>(null)
const processando = ref(false)
const erro = ref('')

const modelo = computed(() => {
  const colunas = ['nome', 'matricula', 'email', 'data_nascimento']
  const exemplo = ['Ana Souza', '2026001', 'ana@exemplo.com', '15/03/2010']
  if (props.mostrarResponsavel) {
    colunas.push('email_responsavel')
    exemplo.push('responsavel.ana@exemplo.com')
  }
  const csv = `${colunas.join(';')}\n${exemplo.join(';')}\n`
  return URL.createObjectURL(new Blob(['﻿', csv], { type: 'text/csv;charset=utf-8' }))
})

async function enviar(simular: boolean): Promise<ImportacaoResultado> {
  const params = { path: { turma_id: props.turmaId } }
  const body = { conteudo: conteudo.value, simular }
  return exigir(api.POST('/api/turmas/{turma_id}/estudantes/importar', { params, body }))
}

async function escolherArquivo(evento: Event) {
  const arquivo = (evento.target as HTMLInputElement).files?.[0]
  if (!arquivo) return
  erro.value = ''
  previa.value = null
  nomeArquivo.value = arquivo.name
  processando.value = true
  try {
    conteudo.value = await lerArquivoTexto(arquivo)
    previa.value = await enviar(true)
  } catch (e) {
    erro.value = (e as Error).message
  } finally {
    processando.value = false
  }
}

async function confirmar() {
  processando.value = true
  erro.value = ''
  try {
    const resultado = await enviar(false)
    if (resultado.aplicado) {
      emit('importado')
    } else {
      previa.value = resultado
    }
  } catch (e) {
    erro.value = (e as Error).message
  } finally {
    processando.value = false
  }
}
</script>

<template>
  <BrModal titulo="Importar estudantes (CSV)" tamanho="large" @fechar="emit('fechar')">
    <div class="formulario">
      <p class="mb-0">
        Use uma planilha salva como <strong>CSV</strong> (separada por ponto e vírgula ou vírgula),
        com a primeira linha de cabeçalho. Colunas obrigatórias: <strong>nome</strong> e
        <strong>matricula</strong>. Opcionais: email, data_nascimento (dd/mm/aaaa)<template
          v-if="mostrarResponsavel"
          >, email_responsavel</template
        >.
      </p>
      <p class="text-down-01 mb-0">
        Estudantes que já existem (mesma matrícula) são atualizados; campos vazios no arquivo não
        apagam dados já cadastrados. Se alguma linha tiver erro, nada é importado.
        <a :href="modelo" download="modelo-estudantes.csv">Baixar planilha modelo</a>.
      </p>

      <div>
        <input
          ref="seletor"
          type="file"
          accept=".csv,text/csv,text/plain"
          class="sr-only"
          aria-label="Arquivo CSV"
          @change="escolherArquivo"
        />
        <BrButton
          icone="fas fa-upload"
          :carregando="processando && !previa"
          @click="seletor?.click()"
        >
          {{ nomeArquivo ? 'Escolher outro arquivo' : 'Escolher arquivo CSV' }}
        </BrButton>
        <span v-if="nomeArquivo" class="ml-2 text-down-01">{{ nomeArquivo }}</span>
      </div>

      <template v-if="previa">
        <BrMessage v-if="previa.erros.length" estado="danger" titulo="O arquivo tem erros.">
          Corrija as linhas abaixo e escolha o arquivo novamente.
        </BrMessage>
        <BrMessage v-else estado="success" titulo="Arquivo válido.">
          {{ previa.total_linhas }} linha(s): {{ previa.criados }} novo(s) estudante(s),
          {{ previa.atualizados }} atualizado(s), {{ previa.matriculados }} matrícula(s) nova(s)
          nesta turma<template v-if="previa.ja_matriculados">
            e {{ previa.ja_matriculados }} já matriculado(s)</template
          >.
        </BrMessage>

        <ul v-if="previa.erros.length" class="erros">
          <li v-for="e in previa.erros" :key="e.linha">
            <strong>Linha {{ e.linha }}:</strong> {{ e.mensagem }}
          </li>
        </ul>
      </template>

      <BrMessage v-if="erro" estado="danger">{{ erro }}</BrMessage>
    </div>

    <template #rodape>
      <BrButton variante="secondary" @click="emit('fechar')">Cancelar</BrButton>
      <BrButton
        variante="primary"
        :disabled="!previa || previa.erros.length > 0 || previa.total_linhas === 0"
        :carregando="processando && !!previa"
        @click="confirmar"
      >
        Importar
      </BrButton>
    </template>
  </BrModal>
</template>

<style scoped>
.erros {
  max-height: 240px;
  overflow-y: auto;
  margin: 0;
}
</style>
