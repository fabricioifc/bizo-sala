/** 0 = segunda ... 6 = domingo (mesma convenção da API e de `date.weekday()`) */
export const DIAS_SEMANA = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

export const NIVEIS = { EMI: 'Ensino Médio Integrado', GRADUACAO: 'Graduação' } as const
export const REGIMES = { ANUAL: 'Anual', SEMESTRAL: 'Semestral' } as const

/** `2026-03-15` → `15/03/2026`, sem passar por Date (evita erro de fuso). */
export function formatarData(iso: string | null | undefined): string {
  if (!iso) return ''
  const [ano, mes, dia] = iso.split('-')
  return `${dia}/${mes}/${ano}`
}

export function formatarNumero(valor: number, casas = 1): string {
  return valor.toLocaleString('pt-BR', {
    minimumFractionDigits: casas,
    maximumFractionDigits: casas,
  })
}

/**
 * Lê um arquivo de texto em UTF-8; se não for UTF-8 válido, assume Windows-1252
 * (padrão do Excel em português ao salvar CSV).
 */
export async function lerArquivoTexto(arquivo: Blob): Promise<string> {
  // FileReader em vez de Blob.arrayBuffer(): funciona também no jsdom dos testes
  const bytes = await new Promise<ArrayBuffer>((resolve, reject) => {
    const leitor = new FileReader()
    leitor.onload = () => resolve(leitor.result as ArrayBuffer)
    leitor.onerror = () => reject(leitor.error)
    leitor.readAsArrayBuffer(arquivo)
  })
  try {
    return new TextDecoder('utf-8', { fatal: true }).decode(bytes)
  } catch {
    return new TextDecoder('windows-1252').decode(bytes)
  }
}
