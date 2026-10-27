import createClient from 'openapi-fetch'

import type { components, paths } from './schema'

export const api = createClient<paths>({ baseUrl: '', credentials: 'same-origin' })

type Schemas = components['schemas']
export type Usuario = Schemas['UsuarioSaida']
export type Curso = Schemas['CursoSaida']
export type CursoEntrada = Schemas['CursoEntrada']
export type Periodo = Schemas['PeriodoSaida']
export type PeriodoEntrada = Schemas['PeriodoEntrada']
export type DiaNaoLetivo = Schemas['DiaNaoLetivoSaida']
export type Turma = Schemas['TurmaSaida']
export type TurmaEntrada = Schemas['TurmaEntrada']
export type Estudante = Schemas['EstudanteSaida']
export type EstudanteEntrada = Schemas['EstudanteEntrada']
export type ImportacaoResultado = Schemas['ImportacaoResultado']
export type Aula = Schemas['AulaSaida']
export type AulaDoDia = Schemas['AulaDoDia']
export type Chamada = Schemas['ChamadaSaida']
export type RegistroFalta = Schemas['RegistroFalta']
export type CargaHoraria = Schemas['CargaHorariaSaida']
export type FrequenciaEstudante = Schemas['FrequenciaEstudante']
export type RegistroConteudo = Schemas['RegistroConteudoDados']
export type Alerta = Schemas['AlertaSaida']
export type Avaliacao = Schemas['AvaliacaoSaida']
export type AvaliacaoEntrada = Schemas['AvaliacaoEntrada']
export type NotaLancada = Schemas['NotaSaida']
export type NotaEntrada = Schemas['NotaEntrada']
export type Boletim = Schemas['Boletim']
export type MensagemEntrada = Schemas['MensagemEntrada']
export type MensagemResumo = Schemas['MensagemResumo']
export type MensagemDetalhe = Schemas['MensagemDetalhe']
export type PreviaMensagem = Schemas['Previa']
export type Nivel = Curso['nivel']
export type Regime = Curso['regime']

/** Extrai a mensagem de erro padrão do FastAPI (`detail`). */
export function mensagemDeErro(erro: unknown, padrao = 'Erro inesperado'): string {
  if (!erro || typeof erro !== 'object' || !('detail' in erro)) return padrao
  const { detail } = erro
  if (typeof detail === 'string') return detail
  // Erros de validação do Pydantic: [{ loc: [...], msg: '...' }]
  if (Array.isArray(detail) && detail.length > 0) {
    return detail
      .map((d) => (d && typeof d === 'object' && 'msg' in d ? String(d.msg) : ''))
      .filter(Boolean)
      .join('; ')
  }
  return padrao
}

/** Desembrulha a resposta do openapi-fetch, lançando Error com a mensagem da API. */
export async function exigir<T>(
  chamada: Promise<{ data?: T; error?: unknown; response: Response }>,
): Promise<T> {
  const { data, error, response } = await chamada
  if (!response.ok) throw new Error(mensagemDeErro(error, `Erro ${response.status}`))
  return data as T
}
