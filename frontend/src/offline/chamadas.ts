/**
 * Chamada offline: as marcações ficam no IndexedDB do aparelho quando não há
 * conexão e são enviadas depois. O envio é idempotente (PUT substitui a chamada
 * da aula), então reenviar não duplica nada.
 */
import Dexie, { type EntityTable } from 'dexie'

import { api, mensagemDeErro, type Chamada, type RegistroFalta } from '@/api/client'

interface ChamadaPendente {
  aulaId: number
  registros: RegistroFalta[]
  salvaEm: string
}

interface ChamadaEmCache {
  aulaId: number
  dados: Chamada
  atualizadaEm: string
}

class BancoLocal extends Dexie {
  pendentes!: EntityTable<ChamadaPendente, 'aulaId'>
  cache!: EntityTable<ChamadaEmCache, 'aulaId'>

  constructor() {
    super('bizo-sala')
    this.version(1).stores({ pendentes: 'aulaId', cache: 'aulaId' })
  }
}

const banco = new BancoLocal()

/** Falha de rede (fetch rejeitado), diferente de um erro devolvido pela API */
class SemConexao extends Error {}

async function enviar(aulaId: number, registros: RegistroFalta[]): Promise<void> {
  let resposta
  try {
    resposta = await api.PUT('/api/aulas/{aula_id}/chamada', {
      params: { path: { aula_id: aulaId } },
      body: { registros },
    })
  } catch {
    throw new SemConexao()
  }
  if (!resposta.response.ok) {
    throw new Error(mensagemDeErro(resposta.error, `Erro ${resposta.response.status}`))
  }
}

/** Carrega a chamada da API; sem conexão, usa a cópia guardada no aparelho. */
export async function carregarChamada(
  aulaId: number,
): Promise<{ dados: Chamada; offline: boolean; pendente: RegistroFalta[] | null }> {
  const pendente = (await banco.pendentes.get(aulaId))?.registros ?? null
  try {
    const { data, error, response } = await api.GET('/api/aulas/{aula_id}/chamada', {
      params: { path: { aula_id: aulaId } },
    })
    if (!response.ok || !data) throw new Error(mensagemDeErro(error, `Erro ${response.status}`))
    await banco.cache.put({ aulaId, dados: data, atualizadaEm: new Date().toISOString() })
    return { dados: data, offline: false, pendente }
  } catch (e) {
    const emCache = await banco.cache.get(aulaId)
    if (e instanceof TypeError && emCache) return { dados: emCache.dados, offline: true, pendente }
    if (e instanceof TypeError) {
      throw new Error('Sem conexão, e esta chamada não foi aberta antes neste aparelho.')
    }
    throw e
  }
}

/** Envia a chamada; sem conexão, guarda no aparelho para enviar depois. */
export async function salvarChamada(
  aulaId: number,
  registros: RegistroFalta[],
): Promise<'enviada' | 'pendente'> {
  const guardar = () =>
    banco.pendentes.put({ aulaId, registros, salvaEm: new Date().toISOString() })
  if (!navigator.onLine) {
    await guardar()
    return 'pendente'
  }
  try {
    await enviar(aulaId, registros)
    await banco.pendentes.delete(aulaId)
    return 'enviada'
  } catch (e) {
    if (e instanceof SemConexao) {
      await guardar()
      return 'pendente'
    }
    throw e
  }
}

export async function contarPendentes(): Promise<number> {
  return banco.pendentes.count()
}

/**
 * Envia as chamadas guardadas. Para na primeira falha de rede; chamadas que a
 * API recusar (ex.: aula cancelada depois) são descartadas e relatadas.
 */
export async function sincronizarPendentes(): Promise<{ enviadas: number; erros: string[] }> {
  const resultado = { enviadas: 0, erros: [] as string[] }
  for (const p of await banco.pendentes.toArray()) {
    try {
      await enviar(p.aulaId, p.registros)
      resultado.enviadas++
    } catch (e) {
      if (e instanceof SemConexao) break
      resultado.erros.push(`Aula ${p.aulaId}: ${(e as Error).message}`)
    }
    await banco.pendentes.delete(p.aulaId)
  }
  return resultado
}

/** Guarda no aparelho as chamadas indicadas, para abrir mesmo sem conexão. */
export async function prepararOffline(aulaIds: number[]): Promise<void> {
  await Promise.allSettled(aulaIds.map((id) => carregarChamada(id)))
}
