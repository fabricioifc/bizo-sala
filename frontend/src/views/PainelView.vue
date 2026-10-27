<script setup lang="ts">
import { BrCard, BrMessage } from '@/components/govbr'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <h1>Olá, {{ auth.usuario?.nome }}</h1>
  <BrCard>
    <BrMessage estado="info" titulo="Nenhuma turma cadastrada ainda.">
      O cadastro de turmas é o próximo passo.
    </BrMessage>
  </BrCard>
</template>
