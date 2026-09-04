#!/usr/bin/env python3
"""Gera a apostila inteira: motor -> figuras -> Markdown -> .docx -> .pdf.

Uso:
    python3 build.py                              # exemplo padrão
    python3 build.py config/meu_exemplo.yaml      # outro exemplo
    python3 build.py --só-figuras                 # só redesenha
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from desenho import render                     # noqa: E402
from engine import calcular                    # noqa: E402
from engine import formatos as cat             # noqa: E402
from engine.barras import _dev                 # noqa: E402
from engine.normas import PENDENTE, Normas     # noqa: E402

LARGURA_TEXTO_POL = 6.3      # coluna util do .docx, com margens de 2,5 cm


# ---------------------------------------------------------------------------
def n(valor, casas: int = 0) -> str:
    """Número no formato brasileiro, sem zero decimal inutil."""
    if valor is None:
        return "—"
    s = f"{float(valor):.{casas}f}"
    if casas:
        s = s.rstrip("0").rstrip(".")
    return s.replace(".", ",")


def _pendentes(normas: Normas) -> list[tuple[str, str]]:
    """Lista os valores ainda marcados PENDENTE, para o apêndice."""
    achados: list[tuple[str, str]] = []

    def varrer(no, caminho):
        if no == PENDENTE:
            achados.append((caminho, "não consta nas fontes deste projeto"))
        elif isinstance(no, dict):
            for k, v in no.items():
                if k == "fonte":
                    continue
                varrer(v, f"{caminho}.{k}" if caminho else str(k))

    varrer(normas.dados, "")
    return achados


def montar_contexto(r, figs, caminho_cfg: Path) -> dict:
    cfg, geo, det = r.cfg, r.geo, r.detalhamento
    normas = r.normas

    def figura(chave: str) -> str:
        f = figs[chave]
        larg = LARGURA_TEXTO_POL
        # figuras muito altas encolhem para não estourar a pagina
        if f.proporcao > 0.95:
            larg = min(larg, 8.4 / f.proporcao)
        return (f'![**{f.titulo}.** {f.legenda}]({f.png.as_posix()})'
                f'{{width={larg:.2f}in}}\n')

    def quebra() -> str:
        """Quebra de pagina que funciona nos dois caminhos de saida.

        O pandoc entrega o bloco openxml so ao .docx e o bloco html so ao PDF
        de reserva; cada saida ignora o que nao é dela.
        """
        return (
            '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n\n'
            '```{=html}\n<div style="page-break-after:always"></div>\n```\n'
        )

    def formato_de(b):
        return next(x for x in b.formatos_alternativos if x.id == b.formato_adotado)

    def tabela_formatos(familia: str) -> str:
        usados = {}
        for b in det.posicoes:
            if b.familia == familia:
                usados.setdefault(b.formato_adotado, []).append(b.codigo)
        linhas = [
            "| Opção | Quando é boa escolha | A favor | Contra | Neste projeto |",
            "|---|---|---|---|---|",
        ]
        for f in cat.CATALOGO[familia]:
            quais = usados.get(f.id, [])
            marca = ", ".join(quais) if quais else "—"
            linhas.append(
                f"| **{f.id} — {f.nome}** | {f.quando_usar} | {f.vantagem} "
                f"| {f.desvantagem} | {marca} |"
            )
        return "\n".join(linhas) + "\n"

    # tabela lambda / alpha_c, gerada a partir das formulas
    tabela_lambda = [("≤ 50 MPa", n(0.80, 3), n(0.85, 3), n(1.25, 3), n(0.425, 3))]
    for fck, _, _ in normas["bloco_retangular"]["tabela"]:
        if fck <= 50:
            continue
        lam, ac = normas.lambda_(fck), normas.alpha_c(fck)
        tabela_lambda.append(
            (f"{n(fck)} MPa", n(lam, 3), n(ac, 3), n(1 / lam, 3), n(ac / 2, 3))
        )

    tabela_areas = []
    for bit in sorted(normas["areas_nominais_cm2"]["tabela"]):
        a = normas.area_nominal(bit)
        tabela_areas.append([f"Ø{n(bit, 1)}"] + [n(a * k, 2) for k in
                                                 (1, 2, 3, 4, 5, 6, 8, 10)])

    acid = normas["cargas_acidentais_kN_m2"]["tabela"]

    return {
        "cfg": cfg, "geo": geo, "det": det, "flex": r.flexao,
        "esf": r.esforcos, "cargas": r.cargas, "arm": r.armadura,
        "mat": cfg["materiais"], "avisos": r.avisos,
        "anc_r": r.anc_reta, "anc_g": r.anc_gancho,
        "princ": cfg["armaduras"]["principal"],
        "dist": cfg["armaduras"]["distribuicao"],
        "borda": cfg["armaduras"]["borda"],
        "blondel": geo.blondel(normas),
        "esp": geo.espessura_minima(normas),
        "esp_min": normas["espessura_minima_cm"],
        "peso_conc": normas.peso_especifico_concreto(),
        "carga_concentrada": normas["cargas_acidentais_kN_m2"]
                                   ["carga_concentrada_degrau_isolado_kN"]["valor"],
        "tabela_acidental": list(acid.items()),
        "tabela_lambda": tabela_lambda,
        "tabela_areas": tabela_areas,
        "kx_lim_baixo": normas["ductilidade"]["kx_limite"]["ate_50_MPa"],
        "kx_lim_alto": normas["ductilidade"]["kx_limite"]["acima_50_MPa"],
        "esp_max_sec": normas["armadura_distribuicao"]["espacamento_max_cm"],
        "frac_borda": normas["armadura_borda"]["fracao_da_minima"],
        "frac_ext_borda": normas["armadura_borda"]["extensao_fracao_vao_menor"],
        "dev_total": _dev(geo, geo.x0, geo.x3),
        "trechos_rot": list(zip(
            r.esforcos.trechos,
            ("Patamar inferior", "Lance (projeção em planta)", "Patamar superior"),
        )),
        "tem_massa_linear": normas["massa_linear_kg_m"]["tabela"] != PENDENTE,
        "pendentes": _pendentes(normas),
        "nome_config": caminho_cfg.name,
        "n": n, "figura": figura, "formato_de": formato_de, "quebra": quebra,
        "tabela_formatos": tabela_formatos,
    }


# ---------------------------------------------------------------------------
def rodar(cmd: list[str]) -> None:
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(
            f"\nFalhou: {' '.join(cmd[:3])}...\n{r.stdout}\n{r.stderr}"
        )


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("config", nargs="?", default="config/exemplo_padrao.yaml")
    ap.add_argument("--so-figuras", action="store_true")
    ap.add_argument("--saida", default="out")
    args = ap.parse_args()

    caminho_cfg = (RAIZ / args.config) if not Path(args.config).is_absolute() \
        else Path(args.config)
    destino = RAIZ / args.saida
    destino.mkdir(parents=True, exist_ok=True)

    print(f"[1/5] motor de cálculo  ({caminho_cfg.name})")
    r = calcular(caminho_cfg)
    print(f"      Mk = {r.esforcos.Mk:.2f} kN.m   x = {r.flexao.x:.2f} cm   "
          f"Kx = {r.flexao.kx:.3f}   As = {r.flexao.As_por_metro:.2f} cm2/m")
    for a in r.avisos:
        print(f"      aviso: {a.splitlines()[0]}")

    print("[2/5] figuras")
    figs = render.todas(r, destino / "fig")
    print(f"      {len(figs)} figuras em {destino / 'fig'}")
    if args.so_figuras:
        return

    print("[3/5] markdown")
    env = Environment(
        loader=FileSystemLoader(RAIZ / "doc"),
        undefined=StrictUndefined,
        trim_blocks=True, lstrip_blocks=True, keep_trailing_newline=True,
    )
    md = env.get_template("apostila.md.j2").render(
        **montar_contexto(r, figs, caminho_cfg)
    )
    caminho_md = destino / "apostila.md"
    caminho_md.write_text(md, encoding="utf-8")
    print(f"      {caminho_md}  ({len(md.splitlines())} linhas)")

    nome = r.cfg["saida"]["nome_arquivo"]
    formatos_pedidos = r.cfg["saida"]["formatos"]

    print("[4/5] docx")
    docx = destino / f"{nome}.docx"
    cmd = ["pandoc", str(caminho_md), "-o", str(docx),
           "--toc", "--toc-depth=2", "--resource-path", str(RAIZ),
           "-f", "markdown+tex_math_dollars+raw_tex+subscript+superscript"]
    ref = RAIZ / "doc" / "referencia.docx"
    if ref.exists():
        cmd += [f"--reference-doc={ref}"]
    rodar(cmd)
    print(f"      {docx}  ({docx.stat().st_size // 1024} kB)")

    if "pdf" in formatos_pedidos:
        print("[5/5] pdf")
        pdf = destino / f"{nome}.pdf"
        if _pdf_por_libreoffice(docx, destino, pdf):
            print(f"      {pdf}  ({pdf.stat().st_size // 1024} kB)  "
                  f"[LibreOffice: idêntico ao .docx]")
        elif _pdf_por_weasyprint(caminho_md, pdf):
            print(f"      {pdf}  ({pdf.stat().st_size // 1024} kB)  "
                  f"[WeasyPrint: mesmo conteúdo, layout próprio]")
        else:
            print("      Nenhum conversor disponível. Instale libreoffice-writer "
                  "ou `pip install weasyprint`; o .docx já está pronto.")
    else:
        print("[5/5] pdf não pedido em saída.formatos")


def _pdf_por_libreoffice(docx: Path, destino: Path, pdf: Path) -> bool:
    """Caminho preferido: o PDF sai idêntico ao .docx."""
    if not shutil.which("soffice"):
        return False
    pdf.unlink(missing_ok=True)
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "pdf",
         "--outdir", str(destino), str(docx)],
        capture_output=True, text=True, timeout=600,
    )
    return pdf.exists()


def _pdf_por_weasyprint(md: Path, pdf: Path) -> bool:
    """Reserva: markdown -> HTML -> PDF, com o CSS de impressão de doc/."""
    try:
        from weasyprint import CSS, HTML
    except ImportError:
        return False
    html = md.with_suffix(".html")
    cmd = ["pandoc", str(md), "-o", str(html), "--standalone", "--toc",
           "--toc-depth=2", "--mathml", "--embed-resources",
           "--resource-path", str(RAIZ),
           "-f", "markdown+tex_math_dollars+raw_tex+subscript+superscript"]
    css = RAIZ / "doc" / "impressao.css"
    if css.exists():
        cmd += [f"--css={css}"]
    subprocess.run(cmd, capture_output=True, text=True, check=True)
    folhas = [CSS(filename=str(css))] if css.exists() else []
    HTML(filename=str(html)).write_pdf(str(pdf), stylesheets=folhas)
    return pdf.exists()


if __name__ == "__main__":
    main()
