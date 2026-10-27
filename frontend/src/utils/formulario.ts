/** Campo numérico opcional: input vazio ('') vira null para a API. */
export function numeroOuNulo(valor: unknown): number | null {
  return typeof valor === 'number' && !Number.isNaN(valor) ? valor : null
}

/** Campo de texto opcional: string vazia vira null para a API. */
export function textoOuNulo(valor: string | null | undefined): string | null {
  const texto = valor?.trim()
  return texto ? texto : null
}
