import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import BrInput from '../BrInput.vue'

describe('BrInput', () => {
  it('associa o rótulo ao campo e atualiza o v-model', async () => {
    const wrapper = mount(BrInput, {
      props: {
        rotulo: 'E-mail',
        modelValue: '',
        'onUpdate:modelValue': (v: string) => wrapper.setProps({ modelValue: v }),
      },
    })
    const input = wrapper.get('input')
    expect(wrapper.get('label').attributes('for')).toBe(input.attributes('id'))

    await input.setValue('professor@ifc.edu.br')
    expect(wrapper.props('modelValue')).toBe('professor@ifc.edu.br')
  })

  it('alterna a visibilidade da senha', async () => {
    const wrapper = mount(BrInput, { props: { rotulo: 'Senha', type: 'password' } })
    expect(wrapper.get('input').attributes('type')).toBe('password')

    await wrapper.get('button').trigger('click')
    expect(wrapper.get('input').attributes('type')).toBe('text')
    expect(wrapper.get('button').attributes('aria-label')).toBe('Ocultar senha')
  })

  it('liga a mensagem de erro ao campo via aria-describedby', () => {
    const wrapper = mount(BrInput, {
      props: { rotulo: 'Nota', estado: 'danger', mensagem: 'Nota inválida' },
    })
    expect(wrapper.classes()).toContain('danger')
    const idMensagem = wrapper.get('.feedback').attributes('id')
    expect(wrapper.get('input').attributes('aria-describedby')).toBe(idMensagem)
    expect(wrapper.get('input').attributes('aria-invalid')).toBe('true')
  })
})
