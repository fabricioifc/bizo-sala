import { describe, expect, it } from 'vitest'

import { agrupar, desagrupar, montarLinhas, paraRegistros } from '../conteudo'

const DIAS = ['2026-03-04', '2026-03-11', '2026-03-18', '2026-03-25']

describe('montarLinhas', () => {
  it('cria uma linha vazia por dia de aula', () => {
    const linhas = montarLinhas(DIAS, [])
    expect(linhas.map((l) => l.datas)).toEqual(DIAS.map((d) => [d]))
    expect(linhas.every((l) => l.texto === '')).toBe(true)
  })

  it('agrupa os dias cobertos por um mesmo registro', () => {
    const linhas = montarLinhas(DIAS, [
      { data_inicio: '2026-03-04', data_fim: '2026-03-18', texto: 'Laços' },
    ])
    expect(linhas.map((l) => [l.datas.length, l.texto])).toEqual([
      [3, 'Laços'],
      [1, ''],
    ])
  })

  it('mantém registro sem dias de aula no intervalo (ex.: aulas canceladas)', () => {
    const linhas = montarLinhas(DIAS, [
      { data_inicio: '2026-03-05', data_fim: '2026-03-06', texto: 'Visita técnica' },
    ])
    expect(linhas[1]).toEqual({
      datas: [],
      inicio: '2026-03-05',
      fim: '2026-03-06',
      texto: 'Visita técnica',
    })
  })
})

describe('agrupar e desagrupar', () => {
  it('junta linhas vizinhas somando os textos', () => {
    let linhas = montarLinhas(DIAS, [])
    linhas[0]!.texto = 'Variáveis'
    linhas[1]!.texto = 'Tipos'
    linhas = agrupar(linhas, 0)
    expect(linhas).toHaveLength(3)
    expect(linhas[0]).toMatchObject({
      inicio: '2026-03-04',
      fim: '2026-03-11',
      texto: 'Variáveis\nTipos',
    })
  })

  it('separa um grupo em dias, repetindo o texto', () => {
    const linhas = desagrupar(
      montarLinhas(DIAS, [{ data_inicio: '2026-03-04', data_fim: '2026-03-25', texto: 'Projeto' }]),
      0,
    )
    expect(linhas.map((l) => [l.inicio, l.texto])).toEqual(DIAS.map((d) => [d, 'Projeto']))
  })
})

describe('paraRegistros', () => {
  it('envia só as linhas preenchidas, com o intervalo do grupo', () => {
    let linhas = montarLinhas(DIAS, [])
    linhas[2]!.texto = '  Prova  '
    linhas = agrupar(linhas, 2)
    expect(paraRegistros(linhas)).toEqual([
      { data_inicio: '2026-03-18', data_fim: '2026-03-25', texto: 'Prova' },
    ])
  })
})
