"""Acesso ao banco SQLite: conexão, criação do esquema e carga inicial da lista de EPI."""
import base64
import os
import re
import sqlite3
import unicodedata

from flask import current_app, g

# Como o item pede tamanho, seguindo a ficha em papel:
# 0 = não pede · 1 = P/M/G/GG/EXG · 2 = numeração (calçado).
SEM_TAMANHO, TAM_LETRA, TAM_NUMERO = 0, 1, 2

ROTULO_TAMANHO = {
    SEM_TAMANHO: "Não pede tamanho",
    TAM_LETRA: "Tamanho P / M / G / GG / EXG",
    TAM_NUMERO: "Numeração (calçado)",
}

# Lista mestre pré-carregada, exatamente como a ficha em papel: uniforme não tem
# CA, e só camisa, camisa polo, calça e jaleco têm tamanho em letra; o calçado
# vai por numeração e o restante não tem tamanho.
EPI_PADRAO = [
    ("CAMISA",                        "",      TAM_LETRA),
    ("CAMISA POLO",                   "",      TAM_LETRA),
    ("CALÇA",                         "",      TAM_LETRA),
    ("JALECO",                        "",      TAM_LETRA),
    ("CALÇADO DE SEGURANÇA",          "28513", TAM_NUMERO),
    ("PROTETOR AURICULAR PLUG",       "",      SEM_TAMANHO),
    ("PROTETOR AURICULAR CONCHA",     "14235", SEM_TAMANHO),
    ("ÓCULOS DE SEGURANÇA",           "34653", SEM_TAMANHO),
    ("LUVA VAQUETA",                  "16059", SEM_TAMANHO),
    ("LUVA PU",                       "48827", SEM_TAMANHO),
    ("PROTETOR SOLAR",                "",      SEM_TAMANHO),
    ("SORO REIDRATANTE",              "",      SEM_TAMANHO),
    ("MÁSCARA PFF1 COM VÁLVULA",      "38944", SEM_TAMANHO),
    ("CAPACETE COM JUGULAR",          "25883", SEM_TAMANHO),
    ("TALABARTE EM Y COM OBSERVADOR", "46206", SEM_TAMANHO),
    ("BONÉ ÁRABE",                    "",      SEM_TAMANHO),
    ("TOUCA ÁRABE",                   "",      SEM_TAMANHO),
    ("AVENTAL DE RASPA",              "",      SEM_TAMANHO),
    ("COLETE REFLETIVO",              "",      SEM_TAMANHO),
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

    migrar_assinatura_por_item(db)
    corrigir_tamanhos_da_lista(db)
    db.commit()


def corrigir_tamanhos_da_lista(db):
    """A lista mestre saiu errada nas primeiras versões: luva, colete e outros
    apareciam pedindo tamanho, o que não existe na ficha em papel. Isto acerta os
    itens da lista padrão, sem tocar no que o usuário criou ou já ajustou à mão."""
    marca = db.execute("SELECT valor FROM ajustes WHERE chave = 'tamanhos_corrigidos'").fetchone() \
        if db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ajustes'").fetchone() \
        else None
    if marca:
        return
    db.execute("CREATE TABLE IF NOT EXISTS ajustes (chave TEXT PRIMARY KEY, valor TEXT NOT NULL)")
    for nome, _ca, tamanho in EPI_PADRAO:
        db.execute("UPDATE epi_master SET tem_tamanho = ? WHERE nome = ? AND tem_tamanho <> ?",
                   (tamanho, nome, tamanho))
    db.execute("INSERT OR REPLACE INTO ajustes (chave, valor) VALUES ('tamanhos_corrigidos', '1')")


def migrar_assinatura_por_item(db):
    """Bancos criados antes guardavam uma assinatura para a entrega inteira.
    Aqui as colunas passam a existir no item e o que havia é copiado para cada
    material — que é o que a ficha em papel exige."""
    colunas = {c["name"] for c in db.execute("PRAGMA table_info(entrega_itens)")}
    novas = [
        ("assinatura_id", "INTEGER REFERENCES assinaturas(id) ON DELETE SET NULL"),
        ("data_devolucao", "TEXT"),
        ("assinatura_devolucao_id", "INTEGER REFERENCES assinaturas(id) ON DELETE SET NULL"),
    ]
    faltando = [(nome, tipo) for nome, tipo in novas if nome not in colunas]
    for nome, tipo in faltando:
        db.execute(f"ALTER TABLE entrega_itens ADD COLUMN {nome} {tipo}")
    if faltando:
        db.execute(
            "UPDATE entrega_itens SET"
            " assinatura_id = COALESCE(assinatura_id,"
            "     (SELECT e.assinatura_id FROM entregas e WHERE e.id = entrega_itens.entrega_id)),"
            " data_devolucao = COALESCE(data_devolucao,"
            "     (SELECT e.data_devolucao FROM entregas e WHERE e.id = entrega_itens.entrega_id)),"
            " assinatura_devolucao_id = COALESCE(assinatura_devolucao_id,"
            "     (SELECT e.assinatura_devolucao_id FROM entregas e WHERE e.id = entrega_itens.entrega_id))"
        )


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
