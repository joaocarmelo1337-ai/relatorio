import cairosvg, math

# ---- geometria real em cm ----
S=28.0; E=18.5; NS=8; H=12.0; C=2.5
PL=120.0            # patamar inferior
PU=120.0            # patamar superior
FL=S*NS             # 224 projecao do lance
RISE=E*NS           # 148
X0,X1=0.0,PL
X2=X1+FL
X3=X2+PU
alpha=math.atan(RISE/FL); ca=math.cos(alpha); ta=math.tan(alpha)
DV=H/ca                      # 14.38 desnivel vertical da espessura
XK1=X1+(DV-H)/ta             # kink inferior do intradorso
XK2=X2-(DV-H)/ta             # kink superior

def soffit(x):
    if x<=XK1: return -H
    if x>=XK2: return RISE-H
    return -DV+ta*(x-X1)

# ---- projecao para tela ----
MW,MH=1160,880
mx,mtop=70,150
sc=(MW-2*mx)/X3
def PX(x): return mx+x*sc
def PY(y): return mtop+(RISE-y)*sc

def bar(x_ini,x_fim,off,hook_ini=None,hook_fim=None,flat_end=None):
    pts=[]
    if hook_ini is not None:
        pts.append((PX(x_ini),PY(soffit(x_ini)+off+hook_ini)))
    xs=[x_ini]+[v for v in (XK1,XK2) if x_ini<v<x_fim]+[x_fim]
    for x in xs: pts.append((PX(x),PY(soffit(x)+off)))
    if flat_end is not None:
        pts.append((PX(flat_end),PY(soffit(x_fim)+off)))
    if hook_fim is not None:
        xe=flat_end if flat_end else x_fim
        pts.append((PX(xe),PY(soffit(x_fim)+off+hook_fim)))
    return "M "+" L ".join(f"{a:.1f} {b:.1f}" for a,b in pts)

# ---- contornos ----
top=[(X0,0)]
for i in range(NS):
    x=X1+i*S; y=i*E
    if i==0: top.append((X1,0))
    top.append((x,y+E)); top.append((x+S,y+E))
top.append((X3,RISE))
top_d="M "+" L ".join(f"{PX(x):.1f} {PY(y):.1f}" for x,y in top)

sof=[(X0,-H),(XK1,-H),(XK2,RISE-H),(X3,RISE-H)]
sof_d="M "+" L ".join(f"{PX(x):.1f} {PY(y):.1f}" for x,y in sof)
body_d=top_d+" L "+f"{PX(X3):.1f} {PY(RISE-H):.1f}"+" L "+" L ".join(f"{PX(x):.1f} {PY(y):.1f}" for x,y in reversed(sof))+" Z"

M="#C0392B"; SEC="#1F8A70"; ANC="#6C5CE7"; GR="#7f7f7f"; TX="#2f2f2f"

def dimh(xa,xb,y,txt):
    ya=PY(y)
    return (f'<line x1="{PX(xa):.1f}" y1="{ya}" x2="{PX(xb):.1f}" y2="{ya}" stroke="{GR}" stroke-width="0.8" marker-start="url(#t)" marker-end="url(#t)"/>'
            f'<text class="d" x="{(PX(xa)+PX(xb))/2:.1f}" y="{ya-6}" text-anchor="middle">{txt}</text>')

def leader(x,y,tx,ty,txt,col,anchor="start"):
    return (f'<line x1="{tx}" y1="{ty+4}" x2="{PX(x):.1f}" y2="{PY(y):.1f}" stroke="{GR}" stroke-width="0.7" marker-end="url(#a)"/>'
            f'<text class="cal" x="{tx}" y="{ty}" text-anchor="{anchor}" fill="{col}">{txt}</text>')

parts=[]
parts.append(f'<path d="{body_d}" fill="#f4f2ee" stroke="none"/>')
parts.append(f'<path d="{top_d}" fill="none" stroke="{TX}" stroke-width="1.6" stroke-linejoin="round"/>')
parts.append(f'<path d="{sof_d}" fill="none" stroke="{TX}" stroke-width="1.6" stroke-linejoin="round"/>')
parts.append(f'<line x1="{PX(X0):.1f}" y1="{PY(0):.1f}" x2="{PX(X0):.1f}" y2="{PY(-H):.1f}" stroke="{TX}" stroke-width="1.6"/>')
parts.append(f'<line x1="{PX(X3):.1f}" y1="{PY(RISE):.1f}" x2="{PX(X3):.1f}" y2="{PY(RISE-H):.1f}" stroke="{TX}" stroke-width="1.6"/>')

# apoios (vigas)
for (xa,ya) in [(X0,-H),(X3,RISE-H)]:
    w=26*sc; h=30*sc
    px=PX(xa)-(0 if xa==X0 else w); py=PY(ya)
    parts.append(f'<rect x="{px:.1f}" y="{py:.1f}" width="{w:.1f}" height="{h:.1f}" fill="url(#h)" stroke="{TX}" stroke-width="1.2"/>')
parts.append(f'<text class="d" x="{PX(X0)+14:.1f}" y="{PY(-H)+62:.1f}">Vesc1</text>')
parts.append(f'<text class="d" x="{PX(X3)-52:.1f}" y="{PY(RISE-H)+62:.1f}">Vesc2</text>')

# ---- barras ----
parts.append(f'<path d="{bar(8,190,3.0,hook_ini=7)}" fill="none" stroke="{M}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>')
parts.append(f'<path d="{bar(62,300,8.5,hook_ini=7)}" fill="none" stroke="{M}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>')
parts.append(f'<path d="{bar(232,X2,3.0,hook_ini=7,hook_fim=7,flat_end=X3-8)}" fill="none" stroke="{M}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>')

for x in (40,90,165,235,300,370,410,450):
    parts.append(f'<circle cx="{PX(x):.1f}" cy="{PY(soffit(x)+3.0):.1f}" r="4.2" fill="{SEC}"/>')
parts.append(f'<circle cx="{PX(112):.1f}" cy="{PY(soffit(112)+3.0):.1f}" r="4.6" fill="{M}"/>')
for x in (126,140):
    parts.append(f'<circle cx="{PX(x):.1f}" cy="{PY(soffit(x)+6.0):.1f}" r="5" fill="#fff" stroke="{ANC}" stroke-width="2.4"/>')
for x in (330,344):
    parts.append(f'<circle cx="{PX(x):.1f}" cy="{PY(soffit(x)+6.0):.1f}" r="5" fill="#fff" stroke="{ANC}" stroke-width="2.4"/>')

# ---- chamadas ----
parts.append(leader(60,soffit(60)+3.0,PX(46),PY(-H)+52,"N1 · 16 Ø10,0 c/ 7,5 · C=192","#C0392B"))
parts.append(leader(90,soffit(90)+3.0,PX(46),PY(-H)+80,"N4 · 23 Ø6,3 c/ 15 · C=237","#1F8A70"))
parts.append(leader(112,soffit(112)+3.0,PX(46),PY(-H)+108,"N5 · 1 Ø10,0 · C=237","#C0392B"))
parts.append(leader(133,soffit(133)+6.0,PX(46),PY(-H)+136,"N6 · 2 Ø6,3 · canto inferior","#6C5CE7"))
parts.append(leader(230,soffit(230)+8.5,PX(198),PY(soffit(200))+52,"N2 · 16 Ø10,0 c/ 7,5 · C=309","#C0392B"))
parts.append(leader(390,soffit(390)+3.0,PX(322),PY(RISE)-58,"N3 · 16 Ø10,0 c/ 7,5 · C=142","#C0392B"))
parts.append(leader(337,soffit(337)+6.0,PX(372),PY(soffit(337))+70,"N6 · 2 Ø6,3 · canto superior","#6C5CE7"))

# ---- cotas ----
parts.append(dimh(X0,X1,-H-104,"120"))
parts.append(dimh(X1,X2,-H-104,"224  (8 × 28)"))
parts.append(dimh(X2,X3,-H-104,"120"))
parts.append(dimh(X0,X3,-H-134,"464"))
xv=PX(X3)+34
parts.append(f'<line x1="{xv}" y1="{PY(RISE)}" x2="{xv}" y2="{PY(0)}" stroke="{GR}" stroke-width="0.8" marker-start="url(#t)" marker-end="url(#t)"/>')
parts.append(f'<text class="d" x="{xv+8}" y="{(PY(RISE)+PY(0))/2:.1f}">148  (8 × 18,5)</text>')
parts.append(f'<text class="ttl" x="{MW/2}" y="{MH-16}" text-anchor="middle">CORTE A-A\u2019  ·  cotas em cm  ·  laje h = 12 cm  ·  cobrimento 2,5 cm</text>')

svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="{MW}" height="{MH}" viewBox="0 0 {MW} {MH}">
<defs>
<marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 1 L9 5 L0 9 z" fill="{GR}"/></marker>
<marker id="t" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="8" markerHeight="8" orient="auto"><line x1="2" y1="8" x2="8" y2="2" stroke="{GR}" stroke-width="1.2"/></marker>
<pattern id="h" width="7" height="7" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="7" stroke="{GR}" stroke-width="1"/></pattern>
</defs>
<style>text{{font-family:Helvetica,Arial,sans-serif;fill:{TX}}} .d{{font-size:15px;fill:#555}} .cal{{font-size:16px;font-weight:600}} .ttl{{font-size:16px;fill:#666;letter-spacing:0.5px}}</style>
<rect width="{MW}" height="{MH}" fill="#ffffff"/>
{''.join(parts)}
</svg>'''
open("fig/corte_conjunto.svg","w").write(svg)
cairosvg.svg2png(bytestring=svg.encode(), write_to="fig/corte_conjunto.png", scale=1.6)
print("ok")
