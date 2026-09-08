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
    """Abre uma conexao com chaves estrangeiras ligadas e linhas por nome.

    check_same_thread=False porque o Streamlit executa o script em threads
    diferentes a cada interacao, enquanto a conexao fica guardada em cache
    entre elas. Sem isso o SQLite recusa a conexao vinda de outra thread.

    E seguro aqui: o Streamlit executa um script por vez em cada sessao, e o
    sistema roda em um unico notebook, com um unico usuario. O WAL abaixo
    ainda permite que uma leitura corra junto de uma escrita, evitando
    "database is locked" quando ha mais de uma aba aberta.
    """
    caminho = Path(caminho or CAMINHO_BANCO)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(caminho, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    con.execute("PRAGMA journal_mode = WAL")
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
