import { describe, expect, it } from 'vitest'

import { formatarNota, lerNota } from '../notas'

describe('lerNota', () => {
  it('aceita vírgula ou ponto e uma casa decimal', () => {
    expect(lerNota('7,5')).toBe(7.5)
    expect(lerNota(' 10 ')).toBe(10)
    expect(lerNota('0.3')).toBe(0.3)
  })

  it('vazio é sem nota', () => {
    expect(lerNota('')).toBeNull()
  })

  it('rejeita fora de 0 a 10 ou com mais casas', () => {
    expect(lerNota('10,5')).toBe('invalida')
    expect(lerNota('7,25')).toBe('invalida')
    expect(lerNota('-1')).toBe('invalida')
    expect(lerNota('abc')).toBe('invalida')
  })
})

describe('formatarNota', () => {
  it('formata com uma casa e vírgula', () => {
    expect(formatarNota(7)).toBe('7,0')
    expect(formatarNota(6.5)).toBe('6,5')
    expect(formatarNota(null)).toBe('')
  })
})
