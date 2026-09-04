#!/usr/bin/env python3
"""Gera doc/referência.docx - a CAMADA DE APRESENTACAO do documento.

O conteúdo vive em doc/apostila.md.j2; a aparência vive aqui. Este script parte
do reference.docx padrão do pandoc e ajusta fontes, cores, tamanhos e margens.
Rode-o de novo só quando quiser mudar o visual:

    python3 doc/gerar_referencia.py
"""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "doc" / "referencia.docx"

FONTE_TEXTO = "Calibri"
FONTE_TITULO = "Calibri"
ACENTO = "C0392B"       # vermelho dos titulos de nível 1
GRAFITE = "333333"
CINZA = "6C6459"

# meia-pontos (Word usa half-points): 22 = 11 pt
TAMANHOS = {
    "Normal": 21, "BodyText": 21, "FirstParagraph": 21, "Compact": 21,
    "Title": 52, "Subtitle": 28, "Author": 22,
    "Heading1": 30, "Heading2": 25, "Heading3": 22,
    "Caption": 17, "ImageCaption": 17, "TableCaption": 17,
    "Table": 18, "Compact": 20,
}
CORES = {
    "Title": ACENTO, "Heading1": ACENTO, "Heading2": GRAFITE,
    "Heading3": GRAFITE, "Subtitle": CINZA,
    "Caption": CINZA, "ImageCaption": CINZA, "TableCaption": CINZA,
}


def _bloco_estilo(xml: str, style_id: str) -> tuple[int, int] | None:
    m = re.search(rf'<w:style [^>]*w:styleId="{style_id}"[^>]*>', xml)
    if not m:
        return None
    fim = xml.index("</w:style>", m.end())
    return m.start(), fim + len("</w:style>")


def _ajustar(xml: str, style_id: str) -> str:
    faixa = _bloco_estilo(xml, style_id)
    if not faixa:
        return xml
    ini, fim = faixa
    bloco = xml[ini:fim]

    # garante um <w:rPr> no estilo
    if "<w:rPr>" not in bloco:
        bloco = bloco.replace("</w:style>", "<w:rPr></w:rPr></w:style>")

    pecas = []
    fonte = FONTE_TITULO if style_id.startswith(("Heading", "Title", "Subtitle")) \
        else FONTE_TEXTO
    pecas.append(
        f'<w:rFonts w:ascii="{fonte}" w:hAnsi="{fonte}" w:cs="{fonte}"/>'
    )
    if style_id in CORES:
        pecas.append(f'<w:color w:val="{CORES[style_id]}"/>')
    if style_id in TAMANHOS:
        sz = TAMANHOS[style_id]
        pecas.append(f'<w:sz w:val="{sz}"/><w:szCs w:val="{sz}"/>')

    novo = "".join(pecas)
    bloco = re.sub(r"<w:rFonts[^>]*/>", "", bloco)
    bloco = re.sub(r"<w:color[^>]*/>", "", bloco)
    bloco = re.sub(r"<w:sz[^>]*/>", "", bloco)
    bloco = re.sub(r"<w:szCs[^>]*/>", "", bloco)
    bloco = bloco.replace("<w:rPr>", f"<w:rPr>{novo}", 1)
    bloco = bloco.replace("<w:rPr/>", f"<w:rPr>{novo}</w:rPr>", 1)
    return xml[:ini] + bloco + xml[fim:]


def main() -> None:
    base = Path(tempfile.mkdtemp()) / "ref.docx"
    with open(base, "wb") as fh:
        subprocess.run(["pandoc", "--print-default-data-file", "reference.docx"],
                       stdout=fh, check=True)

    trabalho = Path(tempfile.mkdtemp())
    with zipfile.ZipFile(base) as z:
        z.extractall(trabalho)

    estilos = trabalho / "word" / "styles.xml"
    xml = estilos.read_text(encoding="utf-8")
    alvos = ["Normal", "BodyText", "FirstParagraph", "Compact", "Title",
             "Subtitle", "Author", "Heading1", "Heading2", "Heading3",
             "Caption", "ImageCaption", "TableCaption", "Table",
             "BlockText", "TOCHeading"]
    for style_id in alvos:
        xml = _ajustar(xml, style_id)
    estilos.write_text(xml, encoding="utf-8")

    # Pagina A4 com margens de 2,5 cm.
    # A largura util resultante (11906 - 2x1417 = 9072 twips = 6,30 in) e o
    # limite que o pandoc usa para escalar as figuras: e por isso que build.py
    # pede width=6.30in. Mexeu aqui, mexa la tambem.
    A4_LARG, A4_ALT, MARGEM = 11906, 16838, 1417
    sect = (
        f'<w:sectPr>'
        f'<w:pgSz w:w="{A4_LARG}" w:h="{A4_ALT}"/>'
        f'<w:pgMar w:top="{MARGEM}" w:right="{MARGEM}" w:bottom="{MARGEM}" '
        f'w:left="{MARGEM}" w:header="708" w:footer="708" w:gutter="0"/>'
        f'</w:sectPr>'
    )
    doc = trabalho / "word" / "document.xml"
    d = doc.read_text(encoding="utf-8")
    antes = d
    d = re.sub(r"<w:sectPr\s*/>|<w:sectPr>[\s\S]*?</w:sectPr>", sect, d, count=1)
    if d == antes:
        raise SystemExit("nao encontrei o <w:sectPr> da referência do pandoc")
    doc.write_text(d, encoding="utf-8")
    util = (A4_LARG - 2 * MARGEM) / 1440
    print(f"pagina A4, margens 2,5 cm -> largura util {util:.2f} in")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    if DESTINO.exists():
        DESTINO.unlink()
    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED) as z:
        for caminho in sorted(trabalho.rglob("*")):
            if caminho.is_file():
                z.write(caminho, caminho.relative_to(trabalho).as_posix())
    shutil.rmtree(trabalho, ignore_errors=True)
    print(f"referência gerada: {DESTINO} ({DESTINO.stat().st_size // 1024} kB)")


if __name__ == "__main__":
    main()
