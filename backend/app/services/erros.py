class ErroDeNegocio(Exception):
    """Regra de negócio violada. A API responde 422 com a mensagem em `detail`."""

    status_code = 422

    def __init__(self, mensagem: str) -> None:
        super().__init__(mensagem)
        self.mensagem = mensagem


class NaoEncontrado(ErroDeNegocio):
    status_code = 404


class Conflito(ErroDeNegocio):
    """A operação conflita com dados existentes (duplicidade, registro em uso)."""

    status_code = 409
