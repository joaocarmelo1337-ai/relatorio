#!/usr/bin/env python3
"""Gera a planta hidrossanitária (DXF + PNG) e a lista de trechos a partir de casa.json.

Uso:  python gerar_projeto.py [casa.json] [pasta_saida]

O desenho e o futuro motor de cálculo leem o mesmo modelo: trechos.csv sai com
os comprimentos de cada ramal, que é a entrada do dimensionamento.
"""
import csv
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import ezdxf
from ezdxf.enums import TextEntityAlignment

LAYERS = {
    # nome: (cor ACI, espessura 1/100 mm, tipo de linha)
    "PAREDES": (7, 50, "Continuous"),
    "ESQUADRIAS": (7, 18, "Continuous"),
    "AMBIENTES": (8, 13, "Continuous"),
    "LOUCAS": (8, 18, "Continuous"),
    "AGUA_FRIA": (5, 35, "Continuous"),
    "ESGOTO": (30, 35, "DASHED"),
    "CAIXAS": (30, 25, "Continuous"),
    "RESERVATORIO": (5, 35, "Continuous"),
    "TRATAMENTO": (30, 35, "Continuous"),
    "TEXTO": (7, 13, "Continuous"),
    "COTAS": (3, 13, "Continuous"),
}

TXT = 0.16  # altura do texto, em metros


def pasta_modelo():
    return Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("casa.json")


# ---------------------------------------------------------------- paredes

def intervalos_paredes(ambientes, esp):
    """Une as arestas dos ambientes em segmentos únicos (h: y fixo, v: x fixo)."""
    linhas = defaultdict(list)
    for a in ambientes:
        linhas[("h", round(a["y0"], 3))].append((a["x0"], a["x1"]))
        linhas[("h", round(a["y1"], 3))].append((a["x0"], a["x1"]))
        linhas[("v", round(a["x0"], 3))].append((a["y0"], a["y1"]))
        linhas[("v", round(a["x1"], 3))].append((a["y0"], a["y1"]))
    saida = {}
    for chave, ivs in linhas.items():
        ivs.sort()
        fundidos = [list(ivs[0])]
        for ini, fim in ivs[1:]:
            if ini <= fundidos[-1][1] + 1e-9:
                fundidos[-1][1] = max(fundidos[-1][1], fim)
            else:
                fundidos.append([ini, fim])
        # estende as pontas para fechar os cantos da espessura
        saida[chave] = [(i - esp / 2, f + esp / 2) for i, f in fundidos]
    return saida


def subtrai(intervalos, ini, fim):
    res = []
    for a, b in intervalos:
        if fim <= a or ini >= b:
            res.append((a, b))
            continue
        if ini > a:
            res.append((a, ini))
        if fim < b:
            res.append((fim, b))
    return res


def desenha_paredes(msp, modelo):
    esp = modelo["espessura_parede"]
    paredes = intervalos_paredes(modelo["ambientes"], esp)
    for aberturas in (modelo.get("portas", []), modelo.get("janelas", [])):
        for ab in aberturas:
            if ab["parede"] == "h":
                chave, centro = ("h", round(ab["y"], 3)), ab["x"]
            else:
                chave, centro = ("v", round(ab["x"], 3)), ab["y"]
            if chave not in paredes:
                raise ValueError(f"abertura fora de parede: {ab}")
            paredes[chave] = subtrai(paredes[chave], centro - ab["larg"] / 2, centro + ab["larg"] / 2)
    for (orient, c), ivs in paredes.items():
        for a, b in ivs:
            pts = [(a, c), (b, c)] if orient == "h" else [(c, a), (c, b)]
            msp.add_lwpolyline(pts, dxfattribs={"layer": "PAREDES", "const_width": esp})


def desenha_portas(msp, portas):
    for p in portas:
        x, y, l, d = p["x"], p["y"], p["larg"], p["dobra"]
        if p["parede"] == "h":
            dobradica, ponta = (x - l / 2, y), (x - l / 2, y + d * l)
            ini, fim = (0, 90) if d > 0 else (270, 360)
        else:
            dobradica, ponta = (x, y - l / 2), (x + d * l, y - l / 2)
            ini, fim = (0, 90) if d > 0 else (90, 180)
        msp.add_line(dobradica, ponta, dxfattribs={"layer": "ESQUADRIAS"})
        msp.add_arc(dobradica, l, ini, fim, dxfattribs={"layer": "ESQUADRIAS"})


def desenha_janelas(msp, janelas):
    for j in janelas:
        x, y, l = j["x"], j["y"], j["larg"]
        for off in (-0.05, 0.0, 0.05):
            if j["parede"] == "h":
                msp.add_line((x - l / 2, y + off), (x + l / 2, y + off), dxfattribs={"layer": "ESQUADRIAS"})
            else:
                msp.add_line((x + off, y - l / 2), (x + off, y + l / 2), dxfattribs={"layer": "ESQUADRIAS"})


def desenha_ambientes(msp, ambientes):
    for a in ambientes:
        area = (a["x1"] - a["x0"]) * (a["y1"] - a["y0"])
        cx, cy = (a["x0"] + a["x1"]) / 2, (a["y0"] + a["y1"]) / 2 + a.get("dy", 0.35)
        msp.add_text(a["nome"].upper(), height=TXT * 1.1, dxfattribs={"layer": "AMBIENTES"}
                     ).set_placement((cx, cy), align=TextEntityAlignment.MIDDLE_CENTER)
        msp.add_text(f"{area:.2f} m²", height=TXT, dxfattribs={"layer": "AMBIENTES"}
                     ).set_placement((cx, cy - 0.28), align=TextEntityAlignment.MIDDLE_CENTER)


# ---------------------------------------------------------------- peças

def retangulo(msp, x, y, w, d, s, layer="LOUCAS"):
    pts = [(x - w / 2, y), (x + w / 2, y), (x + w / 2, y + s * d), (x - w / 2, y + s * d)]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})


def simbolo(msp, p):
    x, y, s, t = p["x"], p["y"], p["dir"], p["tipo"]
    a = {"layer": "LOUCAS"}
    if t == "bacia":
        retangulo(msp, x, y, 0.38, 0.2, s)
        msp.add_ellipse((x, y + s * 0.48), major_axis=(0, 0.28), ratio=0.19 / 0.28, dxfattribs=a)
    elif t == "lavatorio":
        retangulo(msp, x, y, 0.5, 0.4, s)
        msp.add_circle((x, y + s * 0.2), 0.12, dxfattribs=a)
    elif t == "chuveiro":
        retangulo(msp, x, y, 0.85, 0.85, s)
        msp.add_line((x - 0.425, y), (x + 0.425, y + s * 0.85), dxfattribs=a)
        msp.add_line((x - 0.425, y + s * 0.85), (x + 0.425, y), dxfattribs=a)
        msp.add_circle((x, y + s * 0.15), 0.06, dxfattribs=a)
    elif t == "pia":
        retangulo(msp, x, y, 1.2, 0.55, s)
        retangulo(msp, x - 0.3, y + s * 0.08, 0.4, 0.35, s)
        retangulo(msp, x + 0.05, y + s * 0.08, 0.4, 0.35, s)
    elif t == "tanque":
        retangulo(msp, x, y, 0.6, 0.5, s)
        retangulo(msp, x, y + s * 0.07, 0.46, 0.36, s)
    elif t == "maquina":
        retangulo(msp, x, y, 0.6, 0.6, s)
        msp.add_circle((x, y + s * 0.3), 0.2, dxfattribs=a)
    else:
        raise ValueError(f"tipo de peça desconhecido: {t}")


def ponto_tap(p):
    """Ponto onde a peça recebe a água e despeja o esgoto."""
    return (p["x"], p["y"] + p["dir"] * 0.35)


# ---------------------------------------------------------------- redes

def ponto_mais_proximo(pt, polilinha):
    melhor, dmin, seg_i = None, 1e9, 0
    for i in range(len(polilinha) - 1):
        (ax, ay), (bx, by) = polilinha[i], polilinha[i + 1]
        dx, dy = bx - ax, by - ay
        t = max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / (dx * dx + dy * dy)))
        q = (ax + t * dx, ay + t * dy)
        d = math.dist(pt, q)
        if d < dmin:
            melhor, dmin, seg_i = q, d, i
    return melhor, dmin, seg_i


def desenha_polilinha(msp, pts, layer):
    msp.add_lwpolyline(pts, dxfattribs={"layer": layer})


def desenha_redes(msp, modelo, trechos):
    cx = modelo["caixa_dagua"]
    # água fria: tronco + ramais perpendiculares
    tronco = modelo["tronco_agua_fria"]
    desenha_polilinha(msp, tronco, "AGUA_FRIA")
    for i in range(len(tronco) - 1):
        trechos.append(["AF", f"T{i+1}", "tronco", "", round(math.dist(tronco[i], tronco[i + 1]), 2)])
    for p in modelo["pecas"]:
        tap = ponto_tap(p)
        q, dist, _ = ponto_mais_proximo(tap, tronco)
        msp.add_line(q, tap, dxfattribs={"layer": "AGUA_FRIA"})
        msp.add_circle(tap, 0.04, dxfattribs={"layer": "AGUA_FRIA"})
        trechos.append(["AF", f"R-{p['id']}", "ramal", p["id"], round(dist, 2)])
    # esgoto: ramais até o tronco mais próximo
    for k, tr in enumerate(modelo["troncos_esgoto"], 1):
        desenha_polilinha(msp, tr, "ESGOTO")
        for i in range(len(tr) - 1):
            trechos.append(["ES", f"C{k}.{i+1}", "coletor", "", round(math.dist(tr[i], tr[i + 1]), 2)])
    for p in modelo["pecas"]:
        tap = ponto_tap(p)
        troncos = modelo["troncos_esgoto"]
        if "esgoto_tronco" in p:  # força o coletor quando o mais próximo não é o desejado
            troncos = [troncos[p["esgoto_tronco"]]]
        melhor = min((ponto_mais_proximo(tap, tr) for tr in troncos), key=lambda r: r[1])
        msp.add_line(tap, melhor[0], dxfattribs={"layer": "ESGOTO"})
        trechos.append(["ES", f"E-{p['id']}", "ramal", p["id"], round(melhor[1], 2)])
    # caixas
    for c in modelo.get("caixas", []):
        r = 0.25 if c["tipo"] == "CI" else 0.3
        msp.add_circle((c["x"], c["y"]), r, dxfattribs={"layer": "CAIXAS"})
        msp.add_text(c["tipo"], height=0.12, dxfattribs={"layer": "TEXTO"}
                     ).set_placement((c["x"], c["y"] - r - 0.2), align=TextEntityAlignment.MIDDLE_CENTER)
    # etiqueta das peças
    for p in modelo["pecas"]:
        msp.add_text(p["id"], height=0.1, dxfattribs={"layer": "TEXTO"}).set_placement(
            (p["x"], p["y"] + p["dir"] * 0.62), align=TextEntityAlignment.MIDDLE_CENTER)


def desenha_reservatorio(msp, cx):
    pts = [(cx["x0"], cx["y0"]), (cx["x1"], cx["y0"]), (cx["x1"], cx["y1"]), (cx["x0"], cx["y1"])]
    msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "RESERVATORIO", "const_width": 0.08})
    mx, my = (cx["x0"] + cx["x1"]) / 2, (cx["y0"] + cx["y1"]) / 2
    for dy, txt, h in ((0.25, "CAIXA D'ÁGUA", 0.14), (0.0, f"{cx['volume_l']} L", 0.14),
                       (-0.25, f"base em +{cx['cota_base_m']:.2f} m", 0.12)):
        msp.add_text(txt, height=h, dxfattribs={"layer": "TEXTO"}).set_placement(
            (mx, my + dy), align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_text("(torre externa)", height=0.12, dxfattribs={"layer": "TEXTO"}).set_placement(
        (mx, cx["y0"] - 0.25), align=TextEntityAlignment.MIDDLE_CENTER)


def desenha_tratamento(msp, tr, ci):
    f, fl, s = tr["fossa"], tr["filtro"], tr["sumidouro"]
    for caixa, nome in ((f, "FOSSA SÉPTICA"), (fl, "FILTRO")):
        pts = [(caixa["x0"], caixa["y0"]), (caixa["x1"], caixa["y0"]), (caixa["x1"], caixa["y1"]), (caixa["x0"], caixa["y1"])]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "TRATAMENTO", "const_width": 0.06})
        msp.add_text(nome, height=0.13, dxfattribs={"layer": "TEXTO"}).set_placement(
            ((caixa["x0"] + caixa["x1"]) / 2, (caixa["y0"] + caixa["y1"]) / 2), align=TextEntityAlignment.MIDDLE_CENTER)
    msp.add_circle((s["cx"], s["cy"]), s["r"], dxfattribs={"layer": "TRATAMENTO", "lineweight": 60})
    msp.add_text("SUMIDOURO", height=0.13, dxfattribs={"layer": "TEXTO"}).set_placement(
        (s["cx"], s["cy"]), align=TextEntityAlignment.MIDDLE_CENTER)
    ymid_f = (f["y0"] + f["y1"]) / 2
    ymid_fl = (fl["y0"] + fl["y1"]) / 2
    desenha_polilinha(msp, [(ci["x"], ci["y"]), (ci["x"], f["y1"])], "ESGOTO")
    desenha_polilinha(msp, [(f["x1"], ymid_f), (fl["x0"], ymid_fl)], "ESGOTO")
    desenha_polilinha(msp, [(fl["x1"], ymid_fl), (s["cx"] - s["r"], s["cy"])], "ESGOTO")
    msp.add_text("dimensões a calcular (NBR 17076)", height=0.11, dxfattribs={"layer": "TEXTO"}).set_placement(
        ((f["x0"] + s["cx"] + s["r"]) / 2, f["y0"] - 0.35), align=TextEntityAlignment.MIDDLE_CENTER)


# ---------------------------------------------------------------- folha

def cotas_gerais(doc, msp, modelo):
    xs = [a["x0"] for a in modelo["ambientes"]] + [a["x1"] for a in modelo["ambientes"]]
    ys = [a["y0"] for a in modelo["ambientes"]] + [a["y1"] for a in modelo["ambientes"]]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    st = doc.dimstyles.duplicate_entry("EZDXF", "PROJ")
    st.dxf.dimtxt, st.dxf.dimasz, st.dxf.dimexe, st.dxf.dimexo, st.dxf.dimdec = 0.16, 0.12, 0.1, 0.05, 2
    st.dxf.dimlfac = 1.0  # o modelo já está em metros
    st.dxf.dimzin, st.dxf.dimdsep, st.dxf.dimpost = 0, ord(','), '<> m'
    msp.add_linear_dim(base=(0, y1 + 0.9), p1=(x0, y1), p2=(x1, y1), dimstyle="PROJ",
                       dxfattribs={"layer": "COTAS"}).render()
    msp.add_linear_dim(base=(x1 + 0.9, 0), p1=(x1, y0), p2=(x1, y1), angle=90, dimstyle="PROJ",
                       dxfattribs={"layer": "COTAS"}).render()


def legenda(msp, modelo, x, y):
    linhas = [
        ("AGUA_FRIA", "Água fria (tronco e ramais)"),
        ("ESGOTO", "Esgoto sanitário (sob o contrapiso)"),
    ]
    msp.add_text("LEGENDA", height=0.2, dxfattribs={"layer": "TEXTO"}).set_placement((x, y))
    for i, (camada, texto) in enumerate(linhas, 1):
        yy = y - 0.5 * i
        msp.add_line((x, yy), (x + 1.2, yy), dxfattribs={"layer": camada})
        msp.add_text(texto, height=TXT, dxfattribs={"layer": "TEXTO"}).set_placement((x + 1.5, yy - 0.06))
    msp.add_text("CI = caixa de inspeção   CG = caixa de gordura", height=TXT,
                 dxfattribs={"layer": "TEXTO"}).set_placement((x, y - 1.7))
    msp.add_text(f"{modelo['moradores']} moradores  |  piso = cota 0,00  |  desenho esquemático, sem escala de execução",
                 height=0.13, dxfattribs={"layer": "TEXTO"}).set_placement((x, y - 2.1))


def norte(msp, x, y):
    msp.add_lwpolyline([(x, y), (x + 0.25, y - 0.8), (x, y - 0.6), (x - 0.25, y - 0.8)], close=True,
                       dxfattribs={"layer": "TEXTO"})
    msp.add_text("N", height=0.25, dxfattribs={"layer": "TEXTO"}).set_placement((x, y + 0.3), align=TextEntityAlignment.MIDDLE_CENTER)


# ---------------------------------------------------------------- saída

def renderiza_png(doc, caminho):
    import matplotlib.pyplot as plt
    from ezdxf.addons.drawing import Frontend, RenderContext, config
    from ezdxf.addons.drawing.matplotlib import MatplotlibBackend

    fig = plt.figure(figsize=(16, 10), dpi=130)
    ax = fig.add_axes([0, 0, 1, 1])
    cfg = config.Configuration(background_policy=config.BackgroundPolicy.WHITE,
                               color_policy=config.ColorPolicy.COLOR)
    Frontend(RenderContext(doc), MatplotlibBackend(ax), config=cfg).draw_layout(doc.modelspace(), finalize=True)
    fig.savefig(caminho, facecolor="white", dpi=260)


def main():
    arq = pasta_modelo()
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else arq.with_name("saida")
    saida.mkdir(parents=True, exist_ok=True)
    modelo = json.loads(arq.read_text(encoding="utf-8"))

    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.M
    doc.header["$LTSCALE"] = 0.3
    for nome, (cor, peso, lt) in LAYERS.items():
        doc.layers.add(nome, color=cor, lineweight=peso, linetype=lt)
    msp = doc.modelspace()

    trechos = []
    desenha_paredes(msp, modelo)
    desenha_portas(msp, modelo.get("portas", []))
    desenha_janelas(msp, modelo.get("janelas", []))
    desenha_ambientes(msp, modelo["ambientes"])
    for p in modelo["pecas"]:
        simbolo(msp, p)
    desenha_reservatorio(msp, modelo["caixa_dagua"])
    desenha_redes(msp, modelo, trechos)
    ci = next(c for c in modelo["caixas"] if c["tipo"] == "CI")
    desenha_tratamento(msp, modelo["tratamento"], ci)
    cotas_gerais(doc, msp, modelo)
    legenda(msp, modelo, -3.4, -6.2)
    norte(msp, 15.8, 7.6)

    doc.saveas(saida / "planta_hidrossanitaria.dxf")
    renderiza_png(doc, saida / "planta_hidrossanitaria.png")
    with open(saida / "trechos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["rede", "trecho", "tipo", "peca", "comprimento_m"])
        w.writerows(trechos)

    for rede, nome in (("AF", "água fria"), ("ES", "esgoto")):
        tot = sum(t[4] for t in trechos if t[0] == rede)
        print(f"{nome}: {sum(1 for t in trechos if t[0] == rede)} trechos, {tot:.1f} m de tubulação")
    print(f"gerado em {saida}")


if __name__ == "__main__":
    main()
