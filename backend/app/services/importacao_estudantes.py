"""Importação de estudantes de uma turma a partir de CSV.

Formato: primeira linha com cabeçalho; separador `;`, `,` ou tabulação (detectado).
Colunas (sem diferenciar maiúsculas/acentos): nome*, matricula*, email,
data_nascimento (dd/mm/aaaa ou aaaa-mm-dd), email_responsavel.

A importação é tudo-ou-nada: se alguma linha tiver erro, nada é gravado.
"""

import csv
import io
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime

from email_validator import EmailNotValidError, validate_email
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Estudante, Turma

ALIASES: dict[str, set[str]] = {
    "nome": {"nome", "nome_completo", "estudante", "aluno", "nome_do_estudante"},
    "matricula": {"matricula", "numero_matricula", "ra"},
    "email": {"email", "e_mail", "email_estudante"},
    "data_nascimento": {"data_nascimento", "data_de_nascimento", "nascimento"},
    "email_responsavel": {"email_responsavel", "e_mail_responsavel", "email_do_responsavel"},
}
OBRIGATORIAS = ("nome", "matricula")


class _PontoEVirgula(csv.excel):
    """Padrão do Excel em português quando o separador não pode ser detectado."""

    delimiter = ";"


@dataclass
class ErroLinha:
    linha: int
    mensagem: str


@dataclass
class ResultadoImportacao:
    total_linhas: int = 0
    criados: int = 0
    atualizados: int = 0
    matriculados: int = 0
    ja_matriculados: int = 0
    erros: list[ErroLinha] = field(default_factory=list)
    aplicado: bool = False


@dataclass
class _Linha:
    numero: int
    nome: str
    matricula: str
    email: str | None
    data_nascimento: date | None
    email_responsavel: str | None


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return "_".join(sem_acento.strip().lower().replace("-", " ").split())


def _mapear_cabecalho(cabecalho: list[str]) -> dict[str, int]:
    indices: dict[str, int] = {}
    for i, coluna in enumerate(cabecalho):
        nome = _normalizar(coluna)
        for campo, aliases in ALIASES.items():
            if nome in aliases and campo not in indices:
                indices[campo] = i
    return indices


def _data(valor: str) -> date:
    for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(valor, formato).date()
        except ValueError:
            continue
    raise ValueError(f"data inválida: {valor!r} (use dd/mm/aaaa)")


def _email(valor: str) -> str:
    try:
        return validate_email(valor, check_deliverability=False).normalized.lower()
    except EmailNotValidError as e:
        raise ValueError(f"e-mail inválido: {valor!r}") from e


def _ler_linhas(conteudo: str, resultado: ResultadoImportacao) -> list[_Linha]:
    texto = conteudo.lstrip("﻿")
    if not texto.strip():
        resultado.erros.append(ErroLinha(1, "Arquivo vazio"))
        return []
    try:
        dialeto: type[csv.Dialect] = csv.Sniffer().sniff(texto.splitlines()[0], delimiters=";,\t")
    except csv.Error:
        dialeto = _PontoEVirgula

    leitor = csv.reader(io.StringIO(texto), dialeto)
    cabecalho = next(leitor)
    indices = _mapear_cabecalho(cabecalho)
    faltando = [c for c in OBRIGATORIAS if c not in indices]
    if faltando:
        resultado.erros.append(
            ErroLinha(1, f"Coluna(s) obrigatória(s) ausente(s): {', '.join(faltando)}")
        )
        return []

    def valor(registro: list[str], campo: str) -> str:
        i = indices.get(campo)
        return registro[i].strip() if i is not None and i < len(registro) else ""

    linhas: list[_Linha] = []
    vistas: dict[str, int] = {}
    for numero, registro in enumerate(leitor, start=2):
        if not any(c.strip() for c in registro):
            continue
        resultado.total_linhas += 1
        nome, matricula = valor(registro, "nome"), valor(registro, "matricula")
        try:
            if not nome:
                raise ValueError("nome vazio")
            if not matricula:
                raise ValueError("matrícula vazia")
            if len(nome) > 150 or len(matricula) > 30:
                raise ValueError("nome ou matrícula longo demais")
            if matricula in vistas:
                raise ValueError(f"matrícula repetida (também na linha {vistas[matricula]})")
            email = valor(registro, "email")
            nascimento = valor(registro, "data_nascimento")
            responsavel = valor(registro, "email_responsavel")
            linha = _Linha(
                numero=numero,
                nome=nome,
                matricula=matricula,
                email=_email(email) if email else None,
                data_nascimento=_data(nascimento) if nascimento else None,
                email_responsavel=_email(responsavel) if responsavel else None,
            )
        except ValueError as e:
            resultado.erros.append(ErroLinha(numero, str(e).capitalize()))
            continue
        vistas[matricula] = numero
        linhas.append(linha)
    return linhas


def importar_estudantes(
    db: Session, turma: Turma, conteudo: str, simular: bool
) -> ResultadoImportacao:
    resultado = ResultadoImportacao()
    linhas = _ler_linhas(conteudo, resultado)

    matriculados_ids = {e.id for e in turma.estudantes}
    existentes = {
        e.matricula: e
        for e in db.scalars(
            select(Estudante).where(Estudante.matricula.in_([linha.matricula for linha in linhas]))
        )
    }

    for linha in linhas:
        estudante = existentes.get(linha.matricula)
        if estudante is None:
            estudante = Estudante(nome=linha.nome, matricula=linha.matricula)
            db.add(estudante)
            resultado.criados += 1
            alterado = False
        else:
            alterado = estudante.nome != linha.nome
        estudante.nome = linha.nome
        # Campos opcionais só sobrescrevem quando vierem preenchidos no CSV
        for campo in ("email", "data_nascimento", "email_responsavel"):
            novo = getattr(linha, campo)
            if novo is not None and getattr(estudante, campo) != novo:
                setattr(estudante, campo, novo)
                alterado = alterado or estudante.id is not None
        if alterado:
            resultado.atualizados += 1

        if estudante.id is not None and estudante.id in matriculados_ids:
            resultado.ja_matriculados += 1
        else:
            turma.estudantes.append(estudante)
            resultado.matriculados += 1

    if simular or resultado.erros:
        db.rollback()
    else:
        db.commit()
        resultado.aplicado = True
    return resultado
