<script setup lang="ts">
import Card from 'primevue/card'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
</script>

<template>
  <h1>Olá, {{ auth.usuario?.nome }}</h1>
  <Card>
    <template #content>
      <p>Nenhuma turma cadastrada ainda.</p>
    </template>
  </Card>
</template>
