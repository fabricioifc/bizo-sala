import { describe, expect, it } from 'vitest'

import { mensagemDeErro } from '../client'

describe('mensagemDeErro', () => {
  it('usa o detail do FastAPI quando existe', () => {
    expect(mensagemDeErro({ detail: 'E-mail ou senha inválidos' })).toBe(
      'E-mail ou senha inválidos',
    )
  })

  it('junta as mensagens de validação do Pydantic', () => {
    expect(mensagemDeErro({ detail: [{ msg: 'campo a' }, { msg: 'campo b' }] })).toBe(
      'campo a; campo b',
    )
  })

  it('usa a mensagem padrão nos demais casos', () => {
    expect(mensagemDeErro(undefined, 'Falhou')).toBe('Falhou')
    expect(mensagemDeErro({ detail: [] }, 'Falhou')).toBe('Falhou')
  })
})
