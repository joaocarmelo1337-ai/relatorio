"""Ambientes de uma residencia.

A lista padrao (tcc/data/ambientes_padrao.csv) e apenas sugestao: o
engenheiro cria, renomeia e remove ambientes conforme a casa que ele tem
pela frente. Casa nenhuma tem exatamente os 21 ambientes da lista.
"""

from datetime import datetime

from tcc.database.seed import ambientes_padrao


def _agora():
    return datetime.now().isoformat(timespec="seconds")


def listar(con, residencia_id):
    """Ambientes da residencia, com a contagem de manifestacoes de cada um."""
    return con.execute(
        "SELECT a.*, "
        "  (SELECT COUNT(*) FROM ocorrencias o "
        "    WHERE o.ambiente_id = a.id AND o.resultado = 'Nao Conforme') AS manifestacoes "
        "FROM ambientes a WHERE a.residencia_id = ? "
        "ORDER BY a.ordem, a.nome",
        (residencia_id,),
    ).fetchall()


def nomes(con, residencia_id):
    return [linha["nome"] for linha in listar(con, residencia_id)]


def sugestoes(con, residencia_id):
    """Ambientes da lista padrao que a residencia ainda nao tem."""
    ja_existem = {nome.casefold() for nome in nomes(con, residencia_id)}
    return [nome for nome in ambientes_padrao() if nome.casefold() not in ja_existem]


def criar(con, residencia_id, nome, **campos):
    """Cria um ambiente. Nome repetido na mesma residencia e recusado."""
    nome = (nome or "").strip()
    if not nome:
        raise ValueError("o ambiente precisa de um nome")
    if nome.casefold() in {n.casefold() for n in nomes(con, residencia_id)}:
        raise ValueError(f"a residência já tem um ambiente chamado “{nome}”")

    proxima_ordem = con.execute(
        "SELECT COALESCE(MAX(ordem), 0) + 1 AS proxima FROM ambientes WHERE residencia_id = ?",
        (residencia_id,),
    ).fetchone()["proxima"]

    colunas = ("localizacao", "piso", "paredes", "teto", "esquadrias",
               "instalacoes", "observacoes")
    valores = [campos.get(coluna) or None for coluna in colunas]
    cursor = con.execute(
        "INSERT INTO ambientes (residencia_id, nome, ordem, "
        + ", ".join(colunas) + ", criado_em) "
        "VALUES (?,?,?," + ",".join("?" * len(colunas)) + ",?)",
        (residencia_id, nome, proxima_ordem, *valores, _agora()),
    )
    return cursor.lastrowid


def criar_varios(con, residencia_id, nomes_novos):
    """Cria vários de uma vez, pulando os que ja existem. Devolve quantos entraram."""
    criados = 0
    for nome in nomes_novos:
        try:
            criar(con, residencia_id, nome)
            criados += 1
        except ValueError:
            continue
    return criados


def renomear(con, residencia_id, ambiente_id, novo_nome):
    novo_nome = (novo_nome or "").strip()
    if not novo_nome:
        raise ValueError("o ambiente precisa de um nome")
    conflito = con.execute(
        "SELECT 1 FROM ambientes WHERE residencia_id = ? AND id <> ? "
        "AND lower(nome) = lower(?)",
        (residencia_id, ambiente_id, novo_nome),
    ).fetchone()
    if conflito:
        raise ValueError(f"a residência já tem um ambiente chamado “{novo_nome}”")
    con.execute("UPDATE ambientes SET nome = ? WHERE id = ?", (novo_nome, ambiente_id))


def manifestacoes_do_ambiente(con, ambiente_id):
    """As manifestacoes registradas no ambiente, para a ficha de cada um."""
    return con.execute(
        "SELECT o.id, o.codigo, o.descricao, o.tipo_manifestacao, "
        "  i.item AS item_catalogo, c.prioridade, c.gut "
        "FROM ocorrencias o "
        "LEFT JOIN itens_catalogo i ON i.id = o.item_catalogo_id "
        "LEFT JOIN classificacoes_gut c ON c.ocorrencia_id = o.id "
        "WHERE o.ambiente_id = ? AND o.resultado = 'Nao Conforme' "
        "ORDER BY c.gut DESC NULLS LAST, o.id",
        (ambiente_id,),
    ).fetchall()


def excluir(con, ambiente_id):
    """Remove o ambiente. As ocorrencias sao preservadas, sem ambiente.

    Apagar um ambiente nao pode apagar manifestacao registrada -- o dado de
    campo vale mais que a organizacao da casa. O esquema usa ON DELETE SET
    NULL justamente para isso; aqui devolvemos quantas ficaram soltas para
    a tela poder avisar antes de confirmar.
    """
    orfas = con.execute(
        "SELECT COUNT(*) AS n FROM ocorrencias WHERE ambiente_id = ?", (ambiente_id,)
    ).fetchone()["n"]
    con.execute("DELETE FROM ambientes WHERE id = ?", (ambiente_id,))
    return orfas
