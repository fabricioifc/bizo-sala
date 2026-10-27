import time
from collections import defaultdict, deque


class LimiteTentativas:
    """Limita falhas de login por chave (IP) numa janela deslizante, em memória."""

    def __init__(self, max_tentativas: int, janela_segundos: int) -> None:
        self.max_tentativas = max_tentativas
        self.janela_segundos = janela_segundos
        self._falhas: dict[str, deque[float]] = defaultdict(deque)

    def _limpar(self, chave: str, agora: float) -> deque[float]:
        falhas = self._falhas[chave]
        while falhas and agora - falhas[0] > self.janela_segundos:
            falhas.popleft()
        return falhas

    def bloqueado(self, chave: str) -> bool:
        return len(self._limpar(chave, time.monotonic())) >= self.max_tentativas

    def registrar_falha(self, chave: str) -> None:
        agora = time.monotonic()
        self._limpar(chave, agora).append(agora)

    def resetar(self, chave: str | None = None) -> None:
        if chave is None:
            self._falhas.clear()
        else:
            self._falhas.pop(chave, None)
