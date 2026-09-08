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


def _mapa_sistemas(con):
    """Nome do sistema como aparece no Excel -> id na tabela sistemas."""
    return {
        linha["nome"]: linha["id"]
        for linha in con.execute("SELECT id, nome FROM sistemas")
    }


def semear_catalogo(con):
    """Os 82 itens da aba 'Catalogo': IT-001..IT-066 e T3-01..T3-16.

    O prazo de garantia mora aqui, no item -- e assim que a planilha do TCC
    organiza, e e o que a aba 'Lancamentos' consulta para decidir a situacao
    da garantia de cada ocorrencia.
    """
    sistemas = _mapa_sistemas(con)
    for linha in _ler_csv("catalogo_itens.csv"):
        con.execute(
            "INSERT OR IGNORE INTO itens_catalogo "
            "(id_item, sistema_id, sistema_texto, item, origem_esperada, "
            " causas_provaveis, procedencia, tipo_falha_nbr, prazo_anos, "
            " nota_enquadramento) VALUES (?,?,?,?,?,?,?,?,?,?)",
            (
                linha["id_item"],
                sistemas.get(linha["sistema"]),
                linha["sistema"],
                linha["item"],
                linha["origem_esperada"] or None,
                linha["causas_provaveis"] or None,
                linha["procedencia"] or None,
                linha["tipo_falha_nbr"] or None,
                _numero(linha["prazo_anos"]),
                linha["nota_enquadramento"] or None,
            ),
        )


def _prazo_em_anos(texto):
    """'5 anos' -> 5.0; 'Na entrega' e '180 dias' -> None (sem prazo em anos)."""
    texto = (texto or "").strip().lower()
    if texto.endswith("anos") or texto.endswith("ano"):
        try:
            return float(texto.split()[0])
        except ValueError:
            return None
    return None


def semear_regras_garantia(con):
    """A sintese de prazos da NBR 17170 (aba 'Sintese prazos'), documental."""
    for linha in _ler_csv("prazos_nbr17170.csv"):
        ja_existe = con.execute(
            "SELECT 1 FROM regras_garantia WHERE componente = ? AND tipo_falha = ?",
            (linha["sistema_componente"], linha["tipo_falha_coberta"]),
        ).fetchone()
        if ja_existe:
            continue
        con.execute(
            "INSERT INTO regras_garantia "
            "(prazo_texto, prazo_anos, componente, tipo_falha) VALUES (?,?,?,?)",
            (
                linha["prazo"],
                _prazo_em_anos(linha["prazo"]),
                linha["sistema_componente"],
                linha["tipo_falha_coberta"],
            ),
        )


def criar_usuario_admin(con, usuario="admin", senha="admin", nome="João Carmelo"):
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
        semear_catalogo(con)
        semear_regras_garantia(con)
        criar_usuario_admin(con, senha=senha_admin)


def itens_sem_prazo(con):
    """Itens do catalogo sem prazo em anos.

    Nao e erro: sao os 16 itens da Tabela 3 (identificacao no ato da entrega)
    e os itens que decorrem de manutencao do usuario. Aparecem como
    'SEM PRAZO TIPIFICADO' no relogio de garantias.
    """
    return con.execute(
        "SELECT COUNT(*) AS n FROM itens_catalogo WHERE prazo_anos IS NULL"
    ).fetchone()["n"]
