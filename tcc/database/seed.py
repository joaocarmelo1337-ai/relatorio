"""Carga inicial: sistemas, ambientes padrao, regras de garantia e usuario.

Enquanto o Excel do TCC nao e importado, estes CSV em tcc/data sao a
fonte inicial. A importacao do Excel substitui/complementa esta carga.
"""

import csv
import hashlib
import hmac
import os
from datetime import datetime
from pathlib import Path

DADOS = Path(__file__).resolve().parent.parent / "data"


def _agora():
    return datetime.now().isoformat(timespec="seconds")


def _ler_csv(nome):
    with open(DADOS / nome, encoding="utf-8") as arquivo:
        return list(csv.DictReader(arquivo))


def _numero(valor):
    valor = (valor or "").strip()
    return float(valor) if valor else None


def gerar_hash(senha, salt=None):
    """PBKDF2-SHA256. Nao guardamos senha em texto puro em lugar nenhum."""
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac(
        "sha256", senha.encode("utf-8"), salt.encode("utf-8"), 200_000
    ).hex()
    return digest, salt


def conferir_senha(senha, senha_hash, salt):
    calculado, _ = gerar_hash(senha, salt)
    return hmac.compare_digest(calculado, senha_hash)


def semear_sistemas(con):
    for linha in _ler_csv("sistemas.csv"):
        con.execute(
            "INSERT OR IGNORE INTO sistemas (codigo, nome, ordem) VALUES (?,?,?)",
            (linha["codigo"], linha["nome"], int(linha["ordem"])),
        )


def semear_regras_garantia(con):
    mapa = {
        linha["codigo"]: linha["id"]
        for linha in con.execute("SELECT id, codigo FROM sistemas")
    }
    for linha in _ler_csv("prazos_garantia.csv"):
        ja_existe = con.execute(
            "SELECT 1 FROM regras_garantia WHERE componente = ? AND tipo_falha = ?",
            (linha["componente"], linha["tipo_falha"]),
        ).fetchone()
        if ja_existe:
            continue
        con.execute(
            "INSERT INTO regras_garantia "
            "(sistema_id, componente, tipo_falha, prazo_anos, fonte, conferido, observacao) "
            "VALUES (?,?,?,?,?,?,?)",
            (
                mapa.get(linha["sistema"]),
                linha["componente"],
                linha["tipo_falha"],
                _numero(linha["prazo_anos"]),
                linha["fonte"],
                int(linha["conferido"]),
                linha["observacao"],
            ),
        )


def criar_usuario_admin(con, usuario="admin", senha="admin", nome="Joao Carmelo"):
    if con.execute("SELECT 1 FROM usuarios WHERE usuario = ?", (usuario,)).fetchone():
        return False
    senha_hash, salt = gerar_hash(senha)
    con.execute(
        "INSERT INTO usuarios (usuario, senha_hash, salt, nome, perfil, criado_em) "
        "VALUES (?,?,?,?,?,?)",
        (usuario, senha_hash, salt, nome, "admin", _agora()),
    )
    return True


def ambientes_padrao():
    """Lista usada para sugerir ambientes ao cadastrar uma residencia."""
    return [linha["nome"] for linha in _ler_csv("ambientes_padrao.csv")]


def origens_anomalia():
    return [linha["nome"] for linha in _ler_csv("origens_anomalia.csv")]


def semear_tudo(con, senha_admin="admin"):
    with con:
        semear_sistemas(con)
        semear_regras_garantia(con)
        criar_usuario_admin(con, senha=senha_admin)


def regras_pendentes_de_conferencia(con):
    """Quantas regras ainda nao foram conferidas contra a NBR 17170."""
    return con.execute(
        "SELECT COUNT(*) AS n FROM regras_garantia WHERE conferido = 0"
    ).fetchone()["n"]
