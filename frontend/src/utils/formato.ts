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

/** Dia da semana (0 = segunda) de uma data ISO, sem depender do fuso */
export function diaDaSemana(iso: string): number {
  const [ano, mes, dia] = iso.split('-').map(Number)
  return (new Date(Date.UTC(ano!, mes! - 1, dia!)).getUTCDay() + 6) % 7
}

/** `2026-03-04` → `Qua, 04/03` */
export function formatarDataCurta(iso: string): string {
  const [, mes, dia] = iso.split('-')
  return `${DIAS_SEMANA[diaDaSemana(iso)]!.slice(0, 3)}, ${dia}/${mes}`
}

export function nomeDoMes(iso: string): string {
  const [ano, mes] = iso.split('-').map(Number)
  const nome = new Date(Date.UTC(ano!, mes! - 1, 1)).toLocaleString('pt-BR', {
    month: 'long',
    timeZone: 'UTC',
  })
  return `${nome.charAt(0).toUpperCase()}${nome.slice(1)} de ${ano}`
}

/** Data de hoje no fuso local, em ISO (`2026-10-27`) */
export function hojeIso(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
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
