"""Geração do PDF da Ficha de Entrega de EPI (reportlab).

A ficha sai em A4 paisagem, no mesmo desenho da planilha que serve de modelo:
título, empresa e dados do funcionário no topo, declaração de responsabilidade,
campo "Ciente em" e a tabela do histórico com as assinaturas. Empresa e logo vêm
das configurações — é a única parte que muda de uma empresa para outra.
"""
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

PAGINA = landscape(A4)
MARGEM = 10 * mm
LARGURA_UTIL = PAGINA[0] - 2 * MARGEM

TAMANHOS = ["P", "M", "G", "GG", "EXG"]

DECLARACAO = [
    "Declaro que recebi da empresa {empresa} o(s) seguinte(s) equipamento(s) de proteção individual:",
    "A – Declaro haver recebido, nesta data, para o meu uso e proteção pessoal em serviço, os equipamentos abaixo "
    "descritos, os quais me comprometo a utilizar de acordo com as orientações técnicas que me foram dadas quanto ao "
    "seu uso, tarefa e locais determinados pela empresa.",
    "B – Responsabilizo-me também pela guarda e conservação dos equipamentos, respondendo pelo eventual "
    "desaparecimento e/ou danos causados por descuido ou mau uso.",
    "C – Comprometo-me ainda a apresentar para troca todo equipamento que, no decorrer do uso, apresentar defeito ou "
    "desgaste natural da utilização.",
    "D – Declaro também estar ciente de que o não uso dos equipamentos abaixo discriminados constitui ato faltoso, "
    "cabível a aplicação das medidas disciplinares por parte da empresa, conforme a Lei 6.514 de 22/12/1977, "
    "artigo 158, parágrafo único da CLT, e a NR-6, item 6.7.1, da Portaria 3.214 de 08/06/1978.",
]

ST_TITULO = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=15, leading=18, alignment=TA_CENTER)
ST_TEXTO = ParagraphStyle("texto", fontName="Helvetica", fontSize=7.6, leading=9.6, alignment=TA_JUSTIFY)
ST_ROTULO = ParagraphStyle("rotulo", fontName="Helvetica", fontSize=6.4, leading=8,
                           textColor=colors.HexColor("#646f7a"))
ST_VALOR = ParagraphStyle("valor", fontName="Helvetica-Bold", fontSize=10.5, leading=13)
ST_VALOR_EMP = ParagraphStyle("valorEmp", fontName="Helvetica-Bold", fontSize=10, leading=12.5)
ST_TH = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=7, leading=9, alignment=TA_CENTER,
                       textColor=colors.white)
ST_TD = ParagraphStyle("td", fontName="Helvetica", fontSize=7.8, leading=9.6)
ST_TD_C = ParagraphStyle("tdc", fontName="Helvetica", fontSize=8, leading=9.6, alignment=TA_CENTER)
ST_ASSIN = ParagraphStyle("assin", fontName="Helvetica", fontSize=7, leading=8.6, alignment=TA_CENTER,
                          textColor=colors.HexColor("#646f7a"))


def _br(iso):
    """'2026-09-08' -> '08/09/2026'."""
    if not iso:
        return ""
    try:
        a, m, d = str(iso)[:10].split("-")
        return f"{d}/{m}/{a}"
    except ValueError:
        return str(iso)


def _num(q):
    try:
        f = float(q)
    except (TypeError, ValueError):
        return ""
    return str(int(f)) if f == int(f) else f"{f:g}".replace(".", ",")


def _imagem(blob, largura_max, altura_max):
    """Flowable de imagem a partir de bytes, encaixada na caixa mantendo a proporção."""
    if not blob:
        return None
    try:
        buf = io.BytesIO(bytes(blob))
        iw, ih = ImageReader(buf).getSize()
    except Exception:
        return None
    if not iw or not ih:
        return None
    escala = min(largura_max / iw, altura_max / ih)
    buf.seek(0)
    return Image(buf, width=iw * escala, height=ih * escala)


def descricao_item(item):
    """Descrição como na ficha em papel: camisa, camisa polo, calça e jaleco saem
    com os tamanhos entre parênteses; calçado sai com a numeração; os demais saem
    só com o nome."""
    tamanho = (item.get("tamanho") or "").strip().upper()
    tipo = int(item.get("tem_tamanho") or 0)
    if tipo not in (1, 2):
        tipo = (1 if tamanho in TAMANHOS else 2) if tamanho else 0

    if tipo == 1:
        marcas = "&nbsp;&nbsp;".join(
            f"{t} (&nbsp;{'<b>X</b>' if t == tamanho else '&nbsp;&nbsp;'}&nbsp;)" for t in TAMANHOS
        )
        return f"{item['nome']}:&nbsp; {marcas}"
    if tipo == 2:
        return f"{item['nome']} — Nº {tamanho or '______'}"
    return item["nome"]


def _faixa(celulas, cortes, alturas_minimas=0):
    """Uma faixa do cabeçalho com rótulo em cima e valor embaixo, em três colunas."""
    linha = []
    for rotulo, valor, estilo in celulas:
        bloco = []
        if rotulo:
            bloco.append(Paragraph(rotulo, ST_ROTULO))
        bloco.append(Paragraph(valor or "&nbsp;", estilo))
        linha.append(bloco)
    t = Table([linha], colWidths=cortes, rowHeights=[alturas_minimas] if alturas_minimas else None)
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.black),
        ("LINEBEFORE", (1, 0), (-1, 0), 0.9, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    return t


def _cabecalho(empresa, funcionario):
    """Faixa do título com a logo à esquerda e as duas faixas de dados."""
    logo = _imagem(empresa["logo"], 38 * mm, 9.5 * mm)
    titulo = Table(
        [[logo or "", Paragraph("FICHA DE ENTREGA DE EPI", ST_TITULO), ""]],
        colWidths=[LARGURA_UTIL * 0.25, LARGURA_UTIL * 0.50, LARGURA_UTIL * 0.25],
        rowHeights=[13 * mm],
    )
    titulo.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))

    cortes = [LARGURA_UTIL * 0.34, LARGURA_UTIL * 0.44, LARGURA_UTIL * 0.22]
    faixa1 = _faixa([
        ("EMPRESA", empresa["nome"] or "", ST_VALOR_EMP),
        ("NOME DO FUNCIONÁRIO", funcionario["nome"], ST_VALOR),
        ("Nº REGISTRO", funcionario["registro"], ST_VALOR),
    ], cortes)
    faixa2 = _faixa([
        ("CNPJ" if empresa["cnpj"] else "", empresa["cnpj"] or "", ST_VALOR_EMP),
        ("CARGO", funcionario["cargo"], ST_VALOR),
        ("SETOR", funcionario["setor"], ST_VALOR),
    ], cortes)
    return [titulo, faixa1, faixa2]


def _declaracao(empresa_nome):
    texto = [Paragraph(DECLARACAO[0].format(empresa=(empresa_nome or "").upper() or "________________________"),
                       ST_TEXTO)]
    for p in DECLARACAO[1:]:
        texto.append(Spacer(1, 2))
        texto.append(Paragraph(p, ST_TEXTO))
    caixa = Table([[texto]], colWidths=[LARGURA_UTIL])
    caixa.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.9, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return caixa


def _ciente(funcionario, assinatura_blob):
    if funcionario["ciente_data"]:
        d, m, a = _br(funcionario["ciente_data"]).split("/")
        ciente = f"CIENTE EM {d} / {m} / {a}"
    else:
        ciente = "CIENTE EM ______ / ______ / __________"

    assin = _imagem(assinatura_blob, LARGURA_UTIL * 0.45, 11 * mm)
    coluna_dir = [assin] if assin else [Spacer(1, 11 * mm)]
    coluna_dir.append(Paragraph("x______________________________________________________", ST_ASSIN))
    coluna_dir.append(Paragraph("ASSINATURA DO FUNCIONÁRIO", ST_ASSIN))

    t = Table(
        [[Paragraph(ciente, ST_VALOR), coluna_dir]],
        colWidths=[LARGURA_UTIL * 0.45, LARGURA_UTIL * 0.55],
    )
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
        ("VALIGN", (1, 0), (1, 0), "BOTTOM"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.black),
        ("LINEBEFORE", (1, 0), (1, 0), 0.9, colors.black),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    return t


def _tabela_entregas(entregas):
    """entregas: lista de dicts {entrega, itens, assinatura, assinatura_devolucao}."""
    larguras = [
        LARGURA_UTIL * 0.085,   # data de entrega
        LARGURA_UTIL * 0.300,   # EPI/uniforme
        LARGURA_UTIL * 0.080,   # CA
        LARGURA_UTIL * 0.050,   # qtde
        LARGURA_UTIL * 0.210,   # assinatura
        LARGURA_UTIL * 0.085,   # data de devolução
        LARGURA_UTIL * 0.190,   # assinatura de devolução
    ]
    dados = [[
        Paragraph("DATA DE<br/>ENTREGA", ST_TH),
        Paragraph("EPI / UNIFORME", ST_TH),
        Paragraph("CA", ST_TH),
        Paragraph("QTDE", ST_TH),
        Paragraph("ASSINATURA", ST_TH),
        Paragraph("DATA DE<br/>DEVOLUÇÃO", ST_TH),
        Paragraph("ASS. DEVOLUÇÃO", ST_TH),
    ]]
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f4858")),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#5a5a5a")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (4, 1), (4, -1), "CENTER"),
        ("ALIGN", (6, 1), (6, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]

    linha = 1
    for bloco in entregas:
        e = bloco["entrega"]
        itens = bloco["itens"] or [{"nome": "—", "ca": "", "quantidade": "", "tamanho": ""}]
        primeira = linha
        for item in itens:
            # cada material tem a sua própria assinatura, como na ficha em papel
            dados.append([
                Paragraph(_br(e["data_entrega"]), ST_TD_C) if linha == primeira else "",
                Paragraph(descricao_item(item), ST_TD),
                Paragraph(item["ca"] or "", ST_TD_C),
                Paragraph(_num(item["quantidade"]), ST_TD_C),
                _imagem(item.get("assinatura"), larguras[4] - 8, 11 * mm) or "",
                Paragraph(_br(item.get("data_devolucao")), ST_TD_C),
                _imagem(item.get("assinatura_devolucao"), larguras[6] - 8, 11 * mm) or "",
            ])
            linha += 1
        ultima = linha - 1
        if ultima > primeira:          # só a data da entrega ocupa as linhas dos materiais
            estilo.append(("SPAN", (0, primeira), (0, ultima)))
        estilo.append(("LINEABOVE", (0, primeira), (-1, primeira), 0.9, colors.black))

    if len(dados) == 1:
        dados.append([Paragraph("Nenhuma entrega registrada.", ST_TD_C), "", "", "", "", "", ""])
        estilo.append(("SPAN", (0, 1), (-1, 1)))

    alturas = [None] + [13 * mm] * (len(dados) - 1)
    t = Table(dados, colWidths=larguras, rowHeights=alturas, repeatRows=1)
    t.setStyle(TableStyle(estilo))
    return t


def _rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7)
    canvas.setFillColor(colors.HexColor("#646f7a"))
    canvas.drawString(MARGEM, 6 * mm, f"Emitido em {date.today().strftime('%d/%m/%Y')}")
    canvas.drawRightString(PAGINA[0] - MARGEM, 6 * mm, f"Página {doc.page}")
    canvas.restoreState()


def gerar_ficha(empresa, funcionario, entregas, assinatura_admissao=None):
    """Devolve os bytes do PDF da ficha de um funcionário."""
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=PAGINA,
        leftMargin=MARGEM, rightMargin=MARGEM, topMargin=MARGEM, bottomMargin=11 * mm,
        title=f"Ficha de Entrega de EPI — {funcionario['nome']}",
        author=empresa["nome"] or "",
    )
    frame = Frame(MARGEM, 11 * mm, LARGURA_UTIL, PAGINA[1] - MARGEM - 11 * mm, id="corpo",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="ficha", frames=[frame], onPage=_rodape)])

    story = _cabecalho(empresa, funcionario)
    story.append(Spacer(1, 4))
    story.append(KeepTogether(_declaracao(empresa["nome"])))
    story.append(_ciente(funcionario, assinatura_admissao))
    story.append(Spacer(1, 7))
    story.append(_tabela_entregas(entregas))

    doc.build(story)
    return buf.getvalue()
