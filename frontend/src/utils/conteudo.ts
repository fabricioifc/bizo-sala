/**
 * Linhas da tela de registro de conteúdo: cada linha cobre um ou mais dias de aula
 * consecutivos (na lista de dias de aula) e tem um texto.
 */

export interface RegistroConteudo {
  data_inicio: string
  data_fim: string
  texto: string
}

export interface Linha {
  /** Dias de aula cobertos (ISO, ordenados). Vazio = registro sem aulas no intervalo. */
  datas: string[]
  inicio: string
  fim: string
  texto: string
}

function linha(datas: string[], texto: string): Linha {
  return { datas, inicio: datas[0]!, fim: datas[datas.length - 1]!, texto }
}

/** Monta as linhas a partir dos dias de aula e dos registros salvos. */
export function montarLinhas(diasDeAula: string[], registros: RegistroConteudo[]): Linha[] {
  const dias = [...new Set(diasDeAula)].sort()
  const linhas: Linha[] = []
  let registroAnterior: RegistroConteudo | undefined

  for (const dia of dias) {
    const registro = registros.find((r) => r.data_inicio <= dia && dia <= r.data_fim)
    const ultima = linhas[linhas.length - 1]
    if (registro && ultima && registro === registroAnterior) {
      ultima.datas.push(dia)
      ultima.fim = dia
    } else {
      linhas.push(linha([dia], registro?.texto ?? ''))
    }
    registroAnterior = registro
  }

  // Registros cujo intervalo não tem mais nenhum dia de aula (ex.: aulas canceladas)
  for (const r of registros) {
    if (!dias.some((d) => r.data_inicio <= d && d <= r.data_fim)) {
      linhas.push({ datas: [], inicio: r.data_inicio, fim: r.data_fim, texto: r.texto })
    }
  }
  return linhas.sort((a, b) => a.inicio.localeCompare(b.inicio))
}

/** Junta a linha `i` com a seguinte. */
export function agrupar(linhas: Linha[], i: number): Linha[] {
  const a = linhas[i]
  const b = linhas[i + 1]
  if (!a || !b) return linhas
  const textos = [a.texto.trim(), b.texto.trim()].filter(Boolean)
  const unida: Linha = {
    datas: [...a.datas, ...b.datas],
    inicio: a.inicio,
    fim: b.fim,
    texto: [...new Set(textos)].join('\n'),
  }
  return [...linhas.slice(0, i), unida, ...linhas.slice(i + 2)]
}

/** Separa a linha `i` em um dia por linha, cada um com o mesmo texto. */
export function desagrupar(linhas: Linha[], i: number): Linha[] {
  const alvo = linhas[i]
  if (!alvo || alvo.datas.length < 2) return linhas
  const separadas = alvo.datas.map((d) => linha([d], alvo.texto))
  return [...linhas.slice(0, i), ...separadas, ...linhas.slice(i + 1)]
}

/** Converte as linhas preenchidas em registros para a API. */
export function paraRegistros(linhas: Linha[]): RegistroConteudo[] {
  return linhas
    .filter((l) => l.texto.trim())
    .map((l) => ({ data_inicio: l.inicio, data_fim: l.fim, texto: l.texto.trim() }))
}
