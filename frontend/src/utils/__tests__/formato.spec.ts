import { describe, expect, it } from 'vitest'

import { formatarData, lerArquivoTexto } from '../formato'

describe('formatarData', () => {
  it('converte ISO para o formato brasileiro', () => {
    expect(formatarData('2026-03-05')).toBe('05/03/2026')
    expect(formatarData(null)).toBe('')
  })
})

describe('lerArquivoTexto', () => {
  it('lê UTF-8', async () => {
    const arquivo = new Blob([new TextEncoder().encode('Matrícula')])
    expect(await lerArquivoTexto(arquivo)).toBe('Matrícula')
  })

  it('cai para Windows-1252 quando não é UTF-8 (CSV do Excel)', async () => {
    // "Matrícula" em Windows-1252: í = 0xED
    const bytes = new Uint8Array([0x4d, 0x61, 0x74, 0x72, 0xed, 0x63, 0x75, 0x6c, 0x61])
    expect(await lerArquivoTexto(new Blob([bytes]))).toBe('Matrícula')
  })
})
