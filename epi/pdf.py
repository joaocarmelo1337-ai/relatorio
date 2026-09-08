"""Geração do PDF da Ficha de Entrega de EPI (reportlab)."""
import io
from datetime import date

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)

MARGEM = 12 * mm
LARGURA_UTIL = A4[0] - 2 * MARGEM

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

ST_TITULO = ParagraphStyle("titulo", fontName="Helvetica-Bold", fontSize=14, leading=17, alignment=TA_CENTER)
ST_EMPRESA = ParagraphStyle("empresa", fontName="Helvetica-Bold", fontSize=11, leading=13)
ST_CNPJ = ParagraphStyle("cnpj", fontName="Helvetica", fontSize=8, leading=10, textColor=colors.HexColor("#555555"))
ST_TEXTO = ParagraphStyle("texto", fontName="Helvetica", fontSize=7.6, leading=9.6, alignment=TA_JUSTIFY)
ST_ROTULO = ParagraphStyle("rotulo", fontName="Helvetica", fontSize=6.5, leading=8, textColor=colors.HexColor("#555555"))
ST_VALOR = ParagraphStyle("valor", fontName="Helvetica-Bold", fontSize=9.5, leading=12)
ST_TH = ParagraphStyle("th", fontName="Helvetica-Bold", fontSize=7.5, leading=9, alignment=TA_CENTER,
                       textColor=colors.white)
ST_TD = ParagraphStyle("td", fontName="Helvetica", fontSize=7.8, leading=9.5)
ST_TD_C = ParagraphStyle("tdc", fontName="Helvetica", fontSize=7.8, leading=9.5, alignment=TA_CENTER)
ST_ASSIN = ParagraphStyle("assin", fontName="Helvetica", fontSize=6.5, leading=8, alignment=TA_CENTER,
                          textColor=colors.HexColor("#555555"))
ST_RODAPE = ParagraphStyle("rodape", fontName="Helvetica", fontSize=6.5, leading=8,
                           textColor=colors.HexColor("#777777"), alignment=TA_CENTER)


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


def _cabecalho(empresa_nome, empresa_cnpj, logo_blob):
    logo = _imagem(logo_blob, 32 * mm, 18 * mm)
    esquerda = [logo] if logo else []
    esquerda.append(Paragraph(empresa_nome or "Empresa não configurada", ST_EMPRESA))
    if empresa_cnpj:
        esquerda.append(Paragraph(f"CNPJ: {empresa_cnpj}", ST_CNPJ))

    t = Table(
        [[esquerda, Paragraph("FICHA DE ENTREGA DE EPI", ST_TITULO)]],
        colWidths=[LARGURA_UTIL * 0.42, LARGURA_UTIL * 0.58],
    )
    t.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.black),
        ("LINEBEFORE", (1, 0), (1, 0), 0.9, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _dados_funcionario(f):
    def campo(rotulo, valor):
        return [Paragraph(rotulo, ST_ROTULO), Paragraph(valor or "&nbsp;", ST_VALOR)]

    linha1 = Table(
        [[campo("NOME DO FUNCIONÁRIO", f["nome"]), campo("Nº REGISTRO", f["registro"])]],
        colWidths=[LARGURA_UTIL * 0.72, LARGURA_UTIL * 0.28],
    )
    linha2 = Table(
        [[campo("CARGO", f["cargo"]), campo("SETOR", f["setor"])]],
        colWidths=[LARGURA_UTIL * 0.72, LARGURA_UTIL * 0.28],
    )
    estilo = TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.9, colors.black),
        ("LINEBEFORE", (1, 0), (1, 0), 0.9, colors.black),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])
    linha1.setStyle(estilo)
    linha2.setStyle(estilo)
    return [linha1, linha2]


def _ciente(f, assinatura_blob):
    if f["ciente_data"]:
        d, m, a = _br(f["ciente_data"]).split("/")
        ciente = f"CIENTE EM {d} / {m} / {a}"
    else:
        ciente = "CIENTE EM ______ / ______ / __________"

    assin = _imagem(assinatura_blob, 55 * mm, 16 * mm)
    coluna_dir = [assin] if assin else [Spacer(1, 12 * mm)]
    coluna_dir.append(Paragraph("x_________________________________________", ST_ASSIN))
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
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _tabela_entregas(entregas):
    """entregas: lista de dicts {entrega, itens, assinatura, assinatura_devolucao}."""
    larguras = [
        LARGURA_UTIL * 0.105,   # data de entrega
        LARGURA_UTIL * 0.300,   # EPI/uniforme
        LARGURA_UTIL * 0.090,   # CA
        LARGURA_UTIL * 0.060,   # qtde
        LARGURA_UTIL * 0.200,   # assinatura
        LARGURA_UTIL * 0.105,   # data de devolução
        LARGURA_UTIL * 0.140,   # assinatura de devolução
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
        ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#666666")),
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
            nome = item["nome"]
            if item["tamanho"]:
                nome = f"{nome} — <b>{item['tamanho']}</b>"
            dados.append([
                Paragraph(_br(e["data_entrega"]), ST_TD_C) if linha == primeira else "",
                Paragraph(nome, ST_TD),
                Paragraph(item["ca"] or "", ST_TD_C),
                Paragraph(_num(item["quantidade"]), ST_TD_C),
                "" if linha > primeira else (_imagem(bloco["assinatura"], larguras[4] - 8, 13 * mm) or ""),
                Paragraph(_br(e["data_devolucao"]), ST_TD_C) if linha == primeira else "",
                "" if linha > primeira else (_imagem(bloco["assinatura_devolucao"], larguras[6] - 8, 13 * mm) or ""),
            ])
            linha += 1
        ultima = linha - 1
        if ultima > primeira:                       # células da entrega ocupam todas as linhas dos itens
            for col in (0, 4, 5, 6):
                estilo.append(("SPAN", (col, primeira), (col, ultima)))
        estilo.append(("LINEABOVE", (0, primeira), (-1, primeira), 0.9, colors.black))

    if len(dados) == 1:
        dados.append([Paragraph("Nenhuma entrega registrada.", ST_TD_C), "", "", "", "", "", ""])
        estilo.append(("SPAN", (0, 1), (-1, 1)))

    t = Table(dados, colWidths=larguras, repeatRows=1)
    t.setStyle(TableStyle(estilo))
    return t


def _rodape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(colors.HexColor("#777777"))
    canvas.drawString(MARGEM, 8 * mm, f"Emitido em {date.today().strftime('%d/%m/%Y')}")
    canvas.drawRightString(A4[0] - MARGEM, 8 * mm, f"Página {doc.page}")
    canvas.restoreState()


def gerar_ficha(empresa, funcionario, entregas, assinatura_admissao=None):
    """Devolve os bytes do PDF da ficha de um funcionário."""
    buf = io.BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=A4,
        leftMargin=MARGEM, rightMargin=MARGEM, topMargin=MARGEM, bottomMargin=14 * mm,
        title=f"Ficha de Entrega de EPI — {funcionario['nome']}",
        author=empresa["nome"] or "",
    )
    frame = Frame(MARGEM, 14 * mm, LARGURA_UTIL, A4[1] - MARGEM - 14 * mm, id="corpo",
                  leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate(id="ficha", frames=[frame], onPage=_rodape)])

    story = [_cabecalho(empresa["nome"], empresa["cnpj"], empresa["logo"]), Spacer(1, 3)]
    story += _dados_funcionario(funcionario)
    story.append(Spacer(1, 5))

    texto = [Paragraph(DECLARACAO[0].format(empresa=(empresa["nome"] or "").upper() or "___________"), ST_TEXTO)]
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
    story.append(KeepTogether(caixa))
    story.append(_ciente(funcionario, assinatura_admissao))
    story.append(Spacer(1, 6))
    story.append(_tabela_entregas(entregas))

    doc.build(story)
    return buf.getvalue()
