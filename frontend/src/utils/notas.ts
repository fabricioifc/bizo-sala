/** Nota como o professor digita: aceita vírgula ou ponto; vazio = sem nota. */
export function lerNota(texto: string): number | null | 'invalida' {
  const limpo = texto.trim().replace(',', '.')
  if (limpo === '') return null
  if (!/^\d{1,2}(\.\d)?$/.test(limpo)) return 'invalida'
  const valor = Number(limpo)
  return valor >= 0 && valor <= 10 ? valor : 'invalida'
}

/** 7.5 → "7,5" */
export function formatarNota(valor: number | null | undefined): string {
  if (valor === null || valor === undefined) return ''
  return valor.toLocaleString('pt-BR', { minimumFractionDigits: 1, maximumFractionDigits: 1 })
}

export const SITUACOES = {
  EM_ANDAMENTO: 'Em andamento',
  APROVADO: 'Aprovado',
  ABAIXO_DA_MEDIA: 'Abaixo da média',
  REPROVADO_POR_FALTA: 'Reprovado por falta',
} as const

export const SUBSTITUICOES = {
  CICLO: 'Nota do trimestre/ciclo',
  AVALIACAO: 'Uma avaliação específica',
  MELHOR: 'A avaliação que mais aumenta a média',
} as const
