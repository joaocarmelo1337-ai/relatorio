"""Conexao e criacao do banco SQLite.

O SQL fica em schema.sql, em SQL portavel, para que a migracao futura
para PostgreSQL seja uma troca de driver e nao uma reescrita.
"""

import sqlite3
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_BANCO = RAIZ / "dados" / "tcc.db"
SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def conectar(caminho=None):
    """Abre uma conexao com chaves estrangeiras ligadas e linhas por nome."""
    caminho = Path(caminho or CAMINHO_BANCO)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(caminho)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def criar_banco(caminho=None):
    """Cria as tabelas se ainda nao existirem. Idempotente."""
    con = conectar(caminho)
    with con:
        con.executescript(SCHEMA.read_text(encoding="utf-8"))
    return con


def tabelas(con):
    linhas = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [linha["name"] for linha in linhas]
