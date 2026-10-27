"""Cálculo de notas: média do ciclo, recuperação/reavaliação e média final.

Regras (Organização Didática do IFC):
- Notas de 0 a 10 com uma casa decimal, arredondando a segunda (art. 206).
- Nota do ciclo: média ponderada pelos pesos das avaliações regulares (art. 209, plano de
  ensino). Avaliações sem nenhuma nota lançada na turma são ignoradas; numa avaliação já
  lançada, estudante sem nota conta 0.
- Recuperação substitui a nota da avaliação ou do ciclo **quando maior** (arts. 212 e 245).
- Média final: média aritmética das notas dos ciclos (art. 217).
"""

from collections.abc import Sequence
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from app.models import Substituicao, TipoAvaliacao

ZERO = Decimal("0")


def arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class AvaliacaoCalculo:
    id: int
    peso: Decimal
    tipo: TipoAvaliacao
    lancada: bool = True
    substituicao: Substituicao | None = None
    substitui_avaliacao_id: int | None = None


@dataclass(frozen=True)
class NotaCalculo:
    valor: Decimal
    substitui_avaliacao_id: int | None = None  # escolha do professor para este estudante


@dataclass(frozen=True)
class SubstituicaoAplicada:
    recuperacao_id: int
    avaliacao_id: int | None  # None = substituiu a nota do ciclo


@dataclass
class ResultadoCiclo:
    media: Decimal | None
    media_sem_recuperacao: Decimal | None
    substituicoes: list[SubstituicaoAplicada] = field(default_factory=list)


def _ponderada(regulares: Sequence[AvaliacaoCalculo], notas: dict[int, Decimal]) -> Decimal:
    soma_pesos = sum((a.peso for a in regulares), ZERO)
    if soma_pesos == 0:
        return ZERO
    return sum((notas[a.id] * a.peso for a in regulares), ZERO) / soma_pesos


def calcular_ciclo(
    avaliacoes: Sequence[AvaliacaoCalculo], notas: dict[int, NotaCalculo]
) -> ResultadoCiclo:
    regulares = [a for a in avaliacoes if a.tipo == TipoAvaliacao.REGULAR and a.lancada]
    if not regulares:
        return ResultadoCiclo(media=None, media_sem_recuperacao=None)

    base = {a.id: notas[a.id].valor if a.id in notas else ZERO for a in regulares}
    sem_recuperacao = arredondar(_ponderada(regulares, base))
    aplicadas: list[SubstituicaoAplicada] = []
    recuperacoes_do_ciclo: list[tuple[int, Decimal]] = []

    for rec in (a for a in avaliacoes if a.tipo == TipoAvaliacao.RECUPERACAO):
        nota = notas.get(rec.id)
        if nota is None:
            continue
        if rec.substituicao == Substituicao.CICLO:
            recuperacoes_do_ciclo.append((rec.id, nota.valor))
            continue

        alvo = nota.substitui_avaliacao_id or rec.substitui_avaliacao_id
        if rec.substituicao == Substituicao.MELHOR and alvo not in base:
            alvo = _melhor_alvo(regulares, base, nota.valor)
        if alvo in base and alvo is not None and nota.valor > base[alvo]:
            base[alvo] = nota.valor
            aplicadas.append(SubstituicaoAplicada(rec.id, alvo))

    media = arredondar(_ponderada(regulares, base))
    for rec_id, valor in recuperacoes_do_ciclo:
        if valor > media:
            media = arredondar(valor)
            aplicadas.append(SubstituicaoAplicada(rec_id, None))
    return ResultadoCiclo(
        media=media, media_sem_recuperacao=sem_recuperacao, substituicoes=aplicadas
    )


def _melhor_alvo(
    regulares: Sequence[AvaliacaoCalculo], base: dict[int, Decimal], valor: Decimal
) -> int | None:
    """Avaliação cuja substituição mais aumenta a média (None se nenhuma aumenta)."""
    melhor: int | None = None
    melhor_media = _ponderada(regulares, base)
    for a in regulares:
        if valor <= base[a.id]:
            continue
        media = _ponderada(regulares, {**base, a.id: valor})
        if media > melhor_media:
            melhor, melhor_media = a.id, media
    return melhor


def media_final(medias_dos_ciclos: Sequence[Decimal | None]) -> Decimal | None:
    """Média aritmética dos ciclos que já têm nota (None se nenhum tem)."""
    validas = [m for m in medias_dos_ciclos if m is not None]
    if not validas:
        return None
    return arredondar(sum(validas, ZERO) / len(validas))
