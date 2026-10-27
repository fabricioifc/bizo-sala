import createClient from 'openapi-fetch'

import type { components, paths } from './schema'

export const api = createClient<paths>({ baseUrl: '', credentials: 'same-origin' })

export type Usuario = components['schemas']['UsuarioSaida']

/** Extrai a mensagem de erro padrão do FastAPI (`detail`). */
export function mensagemDeErro(erro: unknown, padrao = 'Erro inesperado'): string {
  if (erro && typeof erro === 'object' && 'detail' in erro && typeof erro.detail === 'string') {
    return erro.detail
  }
  return padrao
}
