import { describe, expect, it } from 'vitest'

import type { Alerta } from '@/api/client'

import { descreverAlerta, textoParaSisae } from '../alertas'

const ALERTA: Alerta = {
  id: 1,
  turma_id: 1,
  disciplina: 'Web Design',
  turma_nome: 'INFO 1A',
  estudante_id: 1,
  estudante_nome: 'Ana Souza',
  matricula: '2026001',
  email_responsavel: 'mae@exemplo.com',
  tipo: 'CONSECUTIVAS',
  limite: 2,
  data_gatilho: '2026-03-11',
  datas: ['2026-03-04', '2026-03-11'],
  status: 'PENDENTE',
  resolvido_em: null,
  observacao: null,
}

describe('alertas', () => {
  it('descreve o tipo de alerta', () => {
    expect(descreverAlerta(ALERTA)).toBe('2 faltas consecutivas')
    expect(descreverAlerta({ tipo: 'ALTERNADAS', limite: 5 })).toBe('5 faltas alternadas')
  })

  it('monta o texto para o SISAE', () => {
    expect(textoParaSisae(ALERTA)).toBe(
      'Estudante: Ana Souza (matrícula 2026001)\n' +
        'Turma: Web Design – INFO 1A\n' +
        'Situação: 2 faltas consecutivas, sem comparecer às aulas nos dias 04/03/2026, 11/03/2026.\n' +
        'E-mail do responsável: mae@exemplo.com',
    )
  })
})
