import type { Alerta } from '@/api/client'
import { formatarData } from '@/utils/formato'

export function descreverAlerta(alerta: Pick<Alerta, 'tipo' | 'limite'>): string {
  return alerta.tipo === 'CONSECUTIVAS'
    ? `${alerta.limite} faltas consecutivas`
    : `${alerta.limite} faltas alternadas`
}

/** Texto pronto para enviar ao SISAE (e-mail, mensagem ou formulário). */
export function textoParaSisae(alerta: Alerta): string {
  const dias = alerta.datas.map(formatarData).join(', ')
  const linhas = [
    `Estudante: ${alerta.estudante_nome} (matrícula ${alerta.matricula})`,
    `Turma: ${alerta.disciplina} – ${alerta.turma_nome}`,
    `Situação: ${descreverAlerta(alerta)}, sem comparecer às aulas nos dias ${dias}.`,
  ]
  if (alerta.email_responsavel) linhas.push(`E-mail do responsável: ${alerta.email_responsavel}`)
  return linhas.join('\n')
}
