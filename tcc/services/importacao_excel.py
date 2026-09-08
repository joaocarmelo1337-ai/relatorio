"""Importacao da planilha do TCC.

Le o arquivo Checklist_Vistoria_Garantias_TCC.xlsx e carrega no banco:

    Obras                     -> residencias
    Catalogo                  -> itens_catalogo (82 itens, com o prazo de cada um)
    Síntese prazos NBR 17170  -> regras_garantia (sintese documental)
    Lancamentos               -> ocorrencias + classificacoes_gut

A importacao e idempotente pelas chaves da propria planilha (ID_Obra,
ID_Item, ID_Lancamento), entao reimportar uma versao atualizada atualiza
os registros em vez de duplicar.

Requer openpyxl (ver requirements.txt).
"""

from datetime import date, datetime

from tcc.services import gut as servico_gut
from tcc.services import regime as servico_regime

ABA_OBRAS = "Obras"
ABA_CATALOGO = "Catalogo"
ABA_PRAZOS = "Síntese prazos NBR 17170"
ABA_LANCAMENTOS = "Lancamentos"

# Onde comeca a primeira linha de dados de cada aba (as de cima sao titulo,
# nota metodologica e cabecalho).
PRIMEIRA_LINHA = {ABA_OBRAS: 5, ABA_CATALOGO: 5, ABA_PRAZOS: 5, ABA_LANCAMENTOS: 5}


class PlanilhaInvalida(Exception):
    """A planilha nao tem as abas esperadas."""


def _texto(valor):
    if valor is None:
        return None
    texto = str(valor).strip()
    return texto or None


def _data_iso(valor):
    if valor is None or valor == "":
        return None
    if isinstance(valor, datetime):
        return valor.date().isoformat()
    if isinstance(valor, date):
        return valor.isoformat()
    texto = str(valor).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(texto[:10], formato).date().isoformat()
        except ValueError:
            continue
    return None


def _numero(valor):
    if valor is None or valor == "":
        return None
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def _inteiro(valor):
    numero = _numero(valor)
    return int(numero) if numero is not None else None


def _sim_nao(valor):
    texto = (_texto(valor) or "").lower()
    if texto.startswith("s"):
        return 1
    if texto.startswith("n"):
        return 0
    return None


def abrir(caminho):
    import openpyxl

    wb = openpyxl.load_workbook(caminho, data_only=True)
    faltando = [
        aba for aba in (ABA_OBRAS, ABA_CATALOGO, ABA_LANCAMENTOS)
        if aba not in wb.sheetnames
    ]
    if faltando:
        raise PlanilhaInvalida(
            "a planilha nao tem as abas esperadas: " + ", ".join(faltando)
        )
    return wb


def _linhas(wb, aba):
    ws = wb[aba]
    for linha in ws.iter_rows(min_row=PRIMEIRA_LINHA[aba], values_only=True):
        if linha and _texto(linha[0]):
            yield linha


# ------------------------------------------------------------------- obras
def importar_obras(con, wb, agora):
    """Cada linha da aba 'Obras' com identificacao preenchida vira residencia.

    Linhas com o ID pre-preenchido mas sem identificacao sao ignoradas: sao
    as vagas em branco da planilha (UN-01 a UN-15).
    """
    importadas = 0
    for linha in _linhas(wb, ABA_OBRAS):
        id_obra = _texto(linha[0])
        identificacao = _texto(linha[1])
        if not identificacao:
            continue

        protocolo = _data_iso(linha[4])
        valores = {
            "codigo": id_obra,
            "nome": identificacao,
            "endereco": _texto(linha[2]),
            "data_habite_se": _data_iso(linha[3]),
            "data_protocolo": protocolo,
            "regime_normativo": servico_regime.regime_normativo(protocolo),
            "manual_proprietario": _sim_nao(linha[8]),
            "plano_manutencao": _sim_nao(linha[9]),
            "houve_reforma": _sim_nao(linha[10]),
            "observacoes": _texto(linha[11]) if len(linha) > 11 else None,
        }

        existente = con.execute(
            "SELECT id FROM residencias WHERE codigo = ?", (id_obra,)
        ).fetchone()
        if existente:
            atribuicoes = ", ".join(f"{campo} = ?" for campo in valores)
            con.execute(
                f"UPDATE residencias SET {atribuicoes}, atualizado_em = ? WHERE id = ?",
                (*valores.values(), agora, existente["id"]),
            )
        else:
            campos = ", ".join(valores)
            marcas = ", ".join("?" * len(valores))
            con.execute(
                f"INSERT INTO residencias ({campos}, criado_em) VALUES ({marcas}, ?)",
                (*valores.values(), agora),
            )
        importadas += 1

        # a data da vistoria da planilha vira uma vistoria da residencia
        data_vistoria = _data_iso(linha[6])
        if data_vistoria:
            rid = con.execute(
                "SELECT id FROM residencias WHERE codigo = ?", (id_obra,)
            ).fetchone()["id"]
            ja_tem = con.execute(
                "SELECT 1 FROM vistorias WHERE residencia_id = ? AND data_vistoria = ?",
                (rid, data_vistoria),
            ).fetchone()
            if not ja_tem:
                con.execute(
                    "INSERT INTO vistorias (residencia_id, data_vistoria, origem, criado_em) "
                    "VALUES (?,?,?,?)",
                    (rid, data_vistoria, "planilha", agora),
                )
    return importadas


# ---------------------------------------------------------------- catalogo
def importar_catalogo(con, wb):
    sistemas = {
        linha["nome"]: linha["id"]
        for linha in con.execute("SELECT id, nome FROM sistemas")
    }
    importados = 0
    for linha in _linhas(wb, ABA_CATALOGO):
        valores = (
            sistemas.get(_texto(linha[1])),
            _texto(linha[1]),
            _texto(linha[2]),
            _texto(linha[3]),
            _texto(linha[4]),
            _texto(linha[5]),
            _texto(linha[6]),
            _numero(linha[7]),
            _texto(linha[8]),
        )
        id_item = _texto(linha[0])
        existente = con.execute(
            "SELECT id FROM itens_catalogo WHERE id_item = ?", (id_item,)
        ).fetchone()
        if existente:
            con.execute(
                "UPDATE itens_catalogo SET sistema_id=?, sistema_texto=?, item=?, "
                "origem_esperada=?, causas_provaveis=?, procedencia=?, "
                "tipo_falha_nbr=?, prazo_anos=?, nota_enquadramento=? WHERE id=?",
                (*valores, existente["id"]),
            )
        else:
            con.execute(
                "INSERT INTO itens_catalogo (sistema_id, sistema_texto, item, "
                "origem_esperada, causas_provaveis, procedencia, tipo_falha_nbr, "
                "prazo_anos, nota_enquadramento, id_item) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (*valores, id_item),
            )
        importados += 1
    return importados


# ------------------------------------------------------------- lancamentos
def importar_lancamentos(con, wb, agora):
    """Cada lancamento com Ocorrencia = Sim vira uma ocorrencia classificada.

    G, U e T da planilha alimentam classificacoes_gut. O GUT e a prioridade
    sao RECALCULADOS aqui em vez de copiados: se a formula da planilha e a
    do sistema divergirem, a divergencia aparece em vez de passar batido.
    """
    itens = {
        linha["id_item"]: (linha["id"], linha["sistema_id"], linha["prazo_anos"])
        for linha in con.execute(
            "SELECT id, id_item, sistema_id, prazo_anos FROM itens_catalogo"
        )
    }
    obras = {
        linha["codigo"]: (linha["id"], linha["data_habite_se"])
        for linha in con.execute(
            "SELECT id, codigo, data_habite_se FROM residencias WHERE codigo IS NOT NULL"
        )
    }

    from tcc.services import garantias as servico_garantias

    importados, ignorados = 0, []
    for linha in _linhas(wb, ABA_LANCAMENTOS):
        id_lancamento = _texto(linha[0])
        id_obra, id_item = _texto(linha[1]), _texto(linha[2])
        if _sim_nao(linha[4]) != 1:
            continue  # so entram as ocorrencias constatadas
        if id_obra not in obras or id_item not in itens:
            ignorados.append(id_lancamento)
            continue

        residencia_id, habite_se = obras[id_obra]
        item_id, sistema_id, prazo = itens[id_item]
        data_vistoria = _data_iso(linha[3])

        quadro = servico_garantias.avaliar(habite_se, prazo, referencia=data_vistoria)
        ocorrencia_id = _gravar_ocorrencia(
            con, id_lancamento, residencia_id, item_id, sistema_id,
            data_vistoria, _texto(linha[5]), prazo, quadro["situacao"], agora,
        )

        g, u, t = _inteiro(linha[6]), _inteiro(linha[7]), _inteiro(linha[8])
        if None not in (g, u, t):
            _gravar_gut(con, ocorrencia_id, g, u, t, _texto(linha[13]), agora)
        importados += 1
    return importados, ignorados


def _gravar_ocorrencia(con, codigo, residencia_id, item_id, sistema_id,
                       data_vistoria, descricao, prazo, situacao, agora):
    existente = con.execute(
        "SELECT id FROM ocorrencias WHERE codigo = ?", (codigo,)
    ).fetchone()
    valores = (
        residencia_id, item_id, sistema_id, data_vistoria, descricao,
        prazo, situacao,
    )
    if existente:
        con.execute(
            "UPDATE ocorrencias SET residencia_id=?, item_catalogo_id=?, sistema_id=?, "
            "data_constatacao=?, descricao=?, prazo_anos_aplicado=?, "
            "situacao_garantia=?, atualizado_em=? WHERE id=?",
            (*valores, agora, existente["id"]),
        )
        return existente["id"]
    cursor = con.execute(
        "INSERT INTO ocorrencias (residencia_id, item_catalogo_id, sistema_id, "
        "data_constatacao, descricao, prazo_anos_aplicado, situacao_garantia, "
        "codigo, resultado, criado_em) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (*valores, codigo, "Nao Conforme", agora),
    )
    return cursor.lastrowid


def _gravar_gut(con, ocorrencia_id, g, u, t, justificativa, agora):
    resultado = servico_gut.classificar(g, u, t)
    existente = con.execute(
        "SELECT id FROM classificacoes_gut WHERE ocorrencia_id = ?", (ocorrencia_id,)
    ).fetchone()
    if existente:
        con.execute(
            "UPDATE classificacoes_gut SET gravidade=?, urgencia=?, tendencia=?, "
            "gut=?, prioridade=?, justificativa=?, atualizado_em=? WHERE id=?",
            (g, u, t, resultado["gut"], resultado["prioridade"], justificativa,
             agora, existente["id"]),
        )
    else:
        con.execute(
            "INSERT INTO classificacoes_gut (ocorrencia_id, gravidade, urgencia, "
            "tendencia, gut, prioridade, justificativa, criado_em) "
            "VALUES (?,?,?,?,?,?,?,?)",
            (ocorrencia_id, g, u, t, resultado["gut"], resultado["prioridade"],
             justificativa, agora),
        )


# ------------------------------------------------------------------ fachada
def importar(con, caminho):
    """Importa a planilha inteira. Devolve um resumo do que entrou."""
    agora = datetime.now().isoformat(timespec="seconds")
    wb = abrir(caminho)
    with con:
        itens = importar_catalogo(con, wb)
        obras = importar_obras(con, wb, agora)
        lancamentos, ignorados = importar_lancamentos(con, wb, agora)
    return {
        "itens_catalogo": itens,
        "residencias": obras,
        "ocorrencias": lancamentos,
        "lancamentos_ignorados": ignorados,
    }
