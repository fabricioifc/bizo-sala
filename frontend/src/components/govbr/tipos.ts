export type Estado = 'danger' | 'success' | 'warning' | 'info'

export interface Opcao<T> {
  valor: T
  rotulo: string
}
