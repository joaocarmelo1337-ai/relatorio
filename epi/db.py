"""Acesso ao banco SQLite: conexão, criação do esquema e carga inicial da lista de EPI."""
import base64
import os
import re
import sqlite3
import unicodedata

from flask import current_app, g

# Lista mestre pré-carregada. (nome, CA padrão, pede tamanho?)
EPI_PADRAO = [
    ("CAMISA",                        "",      1),
    ("CAMISA POLO",                   "",      1),
    ("CALÇA",                         "",      1),
    ("JALECO",                        "",      1),
    ("CALÇADO DE SEGURANÇA",          "28513", 1),
    ("PROTETOR AURICULAR PLUG",       "",      0),
    ("PROTETOR AURICULAR CONCHA",     "14235", 0),
    ("ÓCULOS DE SEGURANÇA",           "34653", 0),
    ("LUVA VAQUETA",                  "16059", 1),
    ("LUVA PU",                       "48827", 1),
    ("PROTETOR SOLAR",                "",      0),
    ("SORO REIDRATANTE",              "",      0),
    ("MÁSCARA PFF1 COM VÁLVULA",      "38944", 0),
    ("CAPACETE COM JUGULAR",          "25883", 0),
    ("TALABARTE EM Y COM OBSERVADOR", "46206", 0),
    ("BONÉ ÁRABE",                    "",      0),
    ("TOUCA ÁRABE",                   "",      0),
    ("AVENTAL DE RASPA",              "",      0),
    ("COLETE REFLETIVO",              "",      1),
]


def _sem_acento(texto):
    return unicodedata.normalize("NFKD", texto or "").encode("ascii", "ignore").decode().upper()


def _ordem_pt(a, b):
    """Ordenação alfabética ignorando acentos (ÓCULOS sai junto de O, não no fim)."""
    x, y = _sem_acento(a), _sem_acento(b)
    return (x > y) - (x < y)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
        g.db.create_collation("PT", _ordem_pt)
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Cria as tabelas (idempotente) e faz a carga inicial."""
    db = get_db()
    with current_app.open_resource("schema.sql") as f:
        db.executescript(f.read().decode("utf-8"))

    if db.execute("SELECT COUNT(*) FROM empresa").fetchone()[0] == 0:
        db.execute("INSERT INTO empresa (id, nome, cnpj) VALUES (1, '', '')")

    if db.execute("SELECT COUNT(*) FROM epi_master").fetchone()[0] == 0:
        db.executemany(
            "INSERT INTO epi_master (nome, ca, tem_tamanho) VALUES (?, ?, ?)",
            EPI_PADRAO,
        )
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)
        init_db()


# ---------------------------------------------------------------- assinaturas

def salvar_assinatura(data_url):
    """Grava um data-URL do canvas como blob PNG e devolve o id (ou None se vazio)."""
    if not data_url:
        return None
    m = re.match(r"^data:(image/[a-zA-Z+]+);base64,(.+)$", data_url.strip(), re.S)
    if not m:
        return None
    mime, b64 = m.group(1), m.group(2)
    try:
        blob = base64.b64decode(b64)
    except Exception:
        return None
    if len(blob) < 100:            # canvas em branco
        return None
    db = get_db()
    cur = db.execute(
        "INSERT INTO assinaturas (imagem, mime) VALUES (?, ?)",
        (sqlite3.Binary(blob), mime),
    )
    return cur.lastrowid


def apagar_assinatura(assinatura_id):
    if assinatura_id:
        get_db().execute("DELETE FROM assinaturas WHERE id = ?", (assinatura_id,))


def empresa():
    row = get_db().execute("SELECT * FROM empresa WHERE id = 1").fetchone()
    return row
