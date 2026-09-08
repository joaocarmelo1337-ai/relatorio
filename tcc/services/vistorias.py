"""Vistoria em campo: do item verificado à manifestação classificada.

O fluxo é o do TCC:

    residência → ambiente → sistema → item → resultado
                                                 ↓ (Não Conforme)
                                   manifestação → GUT → garantia

O catálogo de 82 itens é o roteiro. Nada aqui decide sozinho: a
classificação GUT é uma proposta que o engenheiro confirma ou altera, e a
situação de garantia é indicativa — ver AVISO em garantias.py.
"""

import json
from datetime import date, datetime

from tcc.services import garantias as servico_garantias
from tcc.services import gut as servico_gut

CONFORME = "Conforme"
NAO_CONFORME = "Nao Conforme"
NAO_APLICAVEL = "Nao Aplicavel"
NAO_VERIFICADO = "Nao Verificado"
RESULTADOS = (CONFORME, NAO_CONFORME, NAO_APLICAVEL, NAO_VERIFICADO)

ORIGENS = (
    "Anomalia endógena",
    "Anomalia exógena",
    "Anomalia funcional",
    "Anomalia natural",
    "Falha de uso",
    "Falha de operação",
    "Falha de manutenção",
    "Indeterminada",
)

# A NBR 16747:2020 classifica em anomalias (endógena, exógena, funcional) e
# falhas (uso, operação, manutenção). "Anomalia natural" vem da literatura
# complementar -- a planilha do TCC registra essa ressalva, e ela precisa
# aparecer na tela para não virar citação indevida da norma.
NOTA_ORIGENS = (
    "A ABNT NBR 16747:2020 (item 5.3.5) classifica as irregularidades em "
    "ANOMALIAS (endógena, exógena e funcional) e FALHAS (de uso, operação ou "
    "manutenção). A categoria “anomalia natural” provém da literatura técnica "
    "complementar e não consta da norma."
)


def _agora():
    return datetime.now().isoformat(timespec="seconds")


def _hoje():
    return date.today().isoformat()


# ------------------------------------------------------------------ vistoria
def criar_vistoria(con, residencia_id, data_vistoria=None, responsavel=None,
                   tipo="Vistoria técnica", condicoes=None, observacoes=None):
    data_vistoria = data_vistoria or _hoje()
    cursor = con.execute(
        "INSERT INTO vistorias (residencia_id, data_vistoria, responsavel, tipo, "
        "condicoes, observacoes, origem, criado_em) VALUES (?,?,?,?,?,?,?,?)",
        (residencia_id, str(data_vistoria)[:10], responsavel, tipo, condicoes,
         observacoes, "plataforma", _agora()),
    )
    registrar_historico(
        con, residencia_id, data_vistoria, "vistoria",
        f"{tipo} realizada", responsavel, "vistorias", cursor.lastrowid,
    )
    return cursor.lastrowid


def vistorias_da_residencia(con, residencia_id):
    return con.execute(
        "SELECT v.*, "
        "  (SELECT COUNT(*) FROM ocorrencias o WHERE o.vistoria_id = v.id "
        "    AND o.resultado = ?) AS manifestacoes "
        "FROM vistorias v WHERE v.residencia_id = ? "
        "ORDER BY v.data_vistoria DESC, v.id DESC",
        (NAO_CONFORME, residencia_id),
    ).fetchall()


# ------------------------------------------------------------------ catalogo
def sistemas_com_itens(con):
    """Sistemas que têm item de verificação, para o seletor da vistoria."""
    return con.execute(
        "SELECT DISTINCT COALESCE(s.nome, i.sistema_texto) AS nome "
        "FROM itens_catalogo i LEFT JOIN sistemas s ON s.id = i.sistema_id "
        "WHERE i.ativo = 1 ORDER BY nome"
    ).fetchall()


def itens_do_sistema(con, sistema_nome):
    return con.execute(
        "SELECT i.* FROM itens_catalogo i LEFT JOIN sistemas s ON s.id = i.sistema_id "
        "WHERE i.ativo = 1 AND COALESCE(s.nome, i.sistema_texto) = ? "
        "ORDER BY i.id_item",
        (sistema_nome,),
    ).fetchall()


def item(con, item_id):
    return con.execute(
        "SELECT * FROM itens_catalogo WHERE id = ?", (item_id,)
    ).fetchone()


# --------------------------------------------------------------- ocorrencia
def _proximo_codigo(con):
    ultimo = con.execute(
        "SELECT codigo FROM ocorrencias WHERE codigo LIKE 'OCO-%' "
        "ORDER BY id DESC LIMIT 1"
    ).fetchone()
    numero = int(ultimo["codigo"].split("-")[1]) + 1 if ultimo else 1
    return f"OCO-{numero:04d}"


def registrar(con, vistoria_id, item_catalogo_id, resultado, ambiente_id=None,
              descricao=None, localizacao=None, possiveis_causas=None,
              origens=None, extensao=None, intensidade=None, medicao=None,
              abertura_mm=None, tipo_manifestacao=None, observacoes=None):
    """Registra o resultado de um item verificado.

    Só o 'Não Conforme' vira manifestação patológica; os demais resultados
    ficam gravados como registro da verificação (o item foi olhado), o que
    importa para o TCC poder dizer quantos itens foram checados.

    A situação da garantia é calculada aqui, na data da vistoria, a partir do
    Habite-se da residência e do prazo do item do catálogo.
    """
    if resultado not in RESULTADOS:
        raise ValueError(f"resultado inválido: {resultado!r}; use um de {RESULTADOS}")

    vistoria = con.execute(
        "SELECT v.*, r.data_habite_se FROM vistorias v "
        "JOIN residencias r ON r.id = v.residencia_id WHERE v.id = ?",
        (vistoria_id,),
    ).fetchone()
    if vistoria is None:
        raise ValueError(f"vistoria {vistoria_id} não existe")

    linha_item = item(con, item_catalogo_id)
    if linha_item is None:
        raise ValueError(f"item de catálogo {item_catalogo_id} não existe")

    prazo = linha_item["prazo_anos"]
    quadro = servico_garantias.avaliar(
        vistoria["data_habite_se"], prazo, referencia=vistoria["data_vistoria"]
    )

    codigo = _proximo_codigo(con) if resultado == NAO_CONFORME else None
    cursor = con.execute(
        "INSERT INTO ocorrencias (codigo, residencia_id, ambiente_id, vistoria_id, "
        "sistema_id, item_catalogo_id, resultado, data_constatacao, "
        "tipo_manifestacao, descricao, localizacao, possiveis_causas, "
        "origem_anomalia, extensao, intensidade, medicao, abertura_mm, "
        "prazo_anos_aplicado, situacao_garantia, observacoes, criado_em) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (codigo, vistoria["residencia_id"], ambiente_id, vistoria_id,
         linha_item["sistema_id"], item_catalogo_id, resultado,
         vistoria["data_vistoria"], tipo_manifestacao or linha_item["item"],
         descricao, localizacao, possiveis_causas,
         json.dumps(list(origens), ensure_ascii=False) if origens else None,
         extensao, intensidade, medicao, abertura_mm, prazo,
         quadro["situacao"], observacoes, _agora()),
    )
    ocorrencia_id = cursor.lastrowid

    if resultado == NAO_CONFORME:
        registrar_historico(
            con, vistoria["residencia_id"], vistoria["data_vistoria"], "ocorrencia",
            f"{codigo} — {linha_item['item']}", descricao, "ocorrencias", ocorrencia_id,
        )
    return ocorrencia_id


def origens_de(ocorrencia):
    """Lê de volta a lista de origens gravada como JSON."""
    bruto = ocorrencia["origem_anomalia"]
    return json.loads(bruto) if bruto else []


def ocorrencia(con, ocorrencia_id):
    return con.execute(
        "SELECT o.*, i.item AS item_catalogo, i.id_item, i.tipo_falha_nbr, "
        "  i.nota_enquadramento, i.causas_provaveis, a.nome AS ambiente, "
        "  COALESCE(s.nome, i.sistema_texto) AS sistema, r.data_habite_se, "
        "  r.nome AS residencia, c.gravidade, c.urgencia, c.tendencia, "
        "  c.gut, c.prioridade, c.justificativa, c.confirmada_por "
        "FROM ocorrencias o "
        "LEFT JOIN itens_catalogo i ON i.id = o.item_catalogo_id "
        "LEFT JOIN ambientes a ON a.id = o.ambiente_id "
        "LEFT JOIN sistemas s ON s.id = o.sistema_id "
        "LEFT JOIN residencias r ON r.id = o.residencia_id "
        "LEFT JOIN classificacoes_gut c ON c.ocorrencia_id = o.id "
        "WHERE o.id = ?",
        (ocorrencia_id,),
    ).fetchone()


def manifestacoes(con, residencia_id=None, vistoria_id=None):
    """Manifestações (Não Conforme), da residência inteira ou de uma vistoria."""
    condicoes, parametros = ["o.resultado = ?"], [NAO_CONFORME]
    if residencia_id is not None:
        condicoes.append("o.residencia_id = ?")
        parametros.append(residencia_id)
    if vistoria_id is not None:
        condicoes.append("o.vistoria_id = ?")
        parametros.append(vistoria_id)
    return con.execute(
        "SELECT o.*, i.item AS item_catalogo, i.id_item, a.nome AS ambiente, "
        "  COALESCE(s.nome, i.sistema_texto) AS sistema, "
        "  c.gut, c.prioridade "
        "FROM ocorrencias o "
        "LEFT JOIN itens_catalogo i ON i.id = o.item_catalogo_id "
        "LEFT JOIN ambientes a ON a.id = o.ambiente_id "
        "LEFT JOIN sistemas s ON s.id = o.sistema_id "
        "LEFT JOIN classificacoes_gut c ON c.ocorrencia_id = o.id "
        "WHERE " + " AND ".join(condicoes) +
        " ORDER BY c.gut DESC NULLS LAST, o.id",
        parametros,
    ).fetchall()


# ---------------------------------------------------------------- matriz GUT
def classificar(con, ocorrencia_id, gravidade, urgencia, tendencia,
                justificativa=None, confirmada_por=None):
    """Grava (ou atualiza) a classificação GUT de uma manifestação.

    O produto e a prioridade são calculados pelo sistema; G, U e T são
    julgamento do engenheiro. `confirmada_por` registra quem assinou.
    """
    resultado = servico_gut.classificar(gravidade, urgencia, tendencia)
    existente = con.execute(
        "SELECT id FROM classificacoes_gut WHERE ocorrencia_id = ?", (ocorrencia_id,)
    ).fetchone()
    if existente:
        con.execute(
            "UPDATE classificacoes_gut SET gravidade=?, urgencia=?, tendencia=?, "
            "gut=?, prioridade=?, justificativa=?, confirmada_por=?, "
            "atualizado_em=? WHERE id=?",
            (gravidade, urgencia, tendencia, resultado["gut"], resultado["prioridade"],
             justificativa, confirmada_por, _agora(), existente["id"]),
        )
    else:
        con.execute(
            "INSERT INTO classificacoes_gut (ocorrencia_id, gravidade, urgencia, "
            "tendencia, gut, prioridade, justificativa, confirmada_por, criado_em) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (ocorrencia_id, gravidade, urgencia, tendencia, resultado["gut"],
             resultado["prioridade"], justificativa, confirmada_por, _agora()),
        )
    return resultado


# ------------------------------------------------------ alerta de garantia
def alerta_de_garantia(con, ocorrencia_id):
    """O diferencial do TCC: manifestação em sistema com garantia acabando.

    Devolve None quando não há o que alertar. Quando há, devolve o quadro
    para a tela montar o aviso e oferecer o registro para assistência técnica.
    """
    linha = ocorrencia(con, ocorrencia_id)
    if linha is None or linha["resultado"] != NAO_CONFORME:
        return None

    quadro = servico_garantias.avaliar(
        linha["data_habite_se"], linha["prazo_anos_aplicado"],
        referencia=linha["data_constatacao"],
    )
    if not servico_garantias.em_alerta(quadro):
        return None

    return {
        "codigo": linha["codigo"],
        "residencia": linha["residencia"],
        "manifestacao": linha["item_catalogo"],
        "sistema": linha["sistema"],
        "ambiente": linha["ambiente"],
        "tipo_falha_nbr": linha["tipo_falha_nbr"],
        "prioridade": linha["prioridade"],
        "gut": linha["gut"],
        **quadro,
    }


def manifestacoes_em_alerta(con, residencia_id=None):
    """Todas as manifestações cuja garantia pede atenção agora."""
    alertas = []
    for linha in manifestacoes(con, residencia_id=residencia_id):
        alerta = alerta_de_garantia(con, linha["id"])
        if alerta:
            alertas.append(alerta)
    return alertas


# ------------------------------------------------------------------ historico
def registrar_historico(con, residencia_id, data_evento, tipo, titulo,
                        detalhe=None, entidade=None, entidade_id=None,
                        usuario=None):
    """Prontuário digital: a linha do tempo da residência."""
    con.execute(
        "INSERT INTO historico (residencia_id, data_evento, tipo, titulo, detalhe, "
        "entidade, entidade_id, usuario, criado_em) VALUES (?,?,?,?,?,?,?,?,?)",
        (residencia_id, str(data_evento)[:10], tipo, titulo, detalhe, entidade,
         entidade_id, usuario, _agora()),
    )


def historico(con, residencia_id):
    return con.execute(
        "SELECT * FROM historico WHERE residencia_id = ? "
        "ORDER BY data_evento, id",
        (residencia_id,),
    ).fetchall()
