import cairosvg, math
S=28.0;E=18.5;NS=8;H=12.0
PL=120.0;PU=120.0;FL=S*NS;RISE=E*NS
X1=PL;X2=X1+FL;X3=X2+PU
al=math.atan(RISE/FL);ca=math.cos(al);ta=math.tan(al)
DV=H/ca;XK1=X1+(DV-H)/ta;XK2=X2-(DV-H)/ta
def soffit(x):
    if x<=XK1: return -H
    if x>=XK2: return RISE-H
    return -DV+ta*(x-X1)
M="#C0392B";SEC="#1F8A70";ANC="#6C5CE7";GR="#7f7f7f";TX="#2f2f2f";AMB="#B9770E"
DEFS=f'''<defs>
<marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 1 L9 5 L0 9 z" fill="{GR}"/></marker>
<marker id="r" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 1 L9 5 L0 9 z" fill="{M}"/></marker>
<pattern id="h" width="7" height="7" patternTransform="rotate(45)" patternUnits="userSpaceOnUse"><line x1="0" y1="0" x2="0" y2="7" stroke="{GR}" stroke-width="1"/></pattern>
</defs>
<style>text{{font-family:Helvetica,Arial,sans-serif;fill:{TX}}} .d{{font-size:15px;fill:#555}} .cal{{font-size:16px;font-weight:600}} .ttl{{font-size:16px;fill:#666}}</style>'''

def build(xa,xb,ya,yb,W,pad,draw_extra,title,fname):
    sc=(W-2*pad)/(xb-xa)
    Hc=int((yb-ya)*sc+2*pad)
    def PX(x): return pad+(x-xa)*sc
    def PY(y): return pad+(yb-y)*sc
    top=[];
    top.append((max(xa,0),0)) if xa<X1 else None
    pts=[]
    if xa< X1: pts.append((xa,0))
    for i in range(NS):
        x=X1+i*S;y=i*E
        if i==0: pts.append((X1,0))
        pts.append((x,y+E));pts.append((x+S,y+E))
    pts.append((X3,RISE))
    topd="M "+" L ".join(f"{PX(x):.1f} {PY(y):.1f}" for x,y in pts)
    sofp=[(max(xa-5,0),-H),(XK1,-H),(XK2,RISE-H),(X3,RISE-H)]
    sofd="M "+" L ".join(f"{PX(x):.1f} {PY(y):.1f}" for x,y in sofp)
    bodyd=topd+" L "+f"{PX(X3):.1f} {PY(RISE-H):.1f}"+" L "+" L ".join(f"{PX(x):.1f} {PY(y):.1f}" for x,y in reversed(sofp))+" Z"
    p=[f'<path d="{bodyd}" fill="#f4f2ee" stroke="none"/>',
       f'<path d="{topd}" fill="none" stroke="{TX}" stroke-width="1.6" stroke-linejoin="round"/>',
       f'<path d="{sofd}" fill="none" stroke="{TX}" stroke-width="1.6" stroke-linejoin="round"/>']
    p+=draw_extra(PX,PY,sc)
    p.append(f'<text class="ttl" x="{W/2}" y="{Hc-14}" text-anchor="middle">{title}</text>')
    svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{Hc}" viewBox="0 0 {W} {Hc}">{DEFS}<rect width="{W}" height="{Hc}" fill="#fff"/>{"".join(p)}</svg>'
    open(f"fig/{fname}.svg","w").write(svg)
    cairosvg.svg2png(bytestring=svg.encode(), write_to=f"fig/{fname}.png", scale=1.6)

def barpath(PX,PY,x_ini,x_fim,off,hook=None):
    pts=[]
    if hook: pts.append((PX(x_ini),PY(soffit(x_ini)+off+hook)))
    xs=[x_ini]+[v for v in (XK1,XK2) if x_ini<v<x_fim]+[x_fim]
    for x in xs: pts.append((PX(x),PY(soffit(x)+off)))
    return "M "+" L ".join(f"{a:.1f} {b:.1f}" for a,b in pts)

# ---- N2 dividida ----
def ex_n2(PX,PY,sc):
    o=[]
    o.append(f'<path d="{barpath(PX,PY,8,150,3.0,hook=7)}" fill="none" stroke="{M}" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<path d="{barpath(PX,PY,62,215,8.5,hook=7)}" fill="none" stroke="{AMB}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<path d="{barpath(PX,PY,180,320,3.0)}" fill="none" stroke="{M}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round"/>')
    o.append(f'<path d="{barpath(PX,PY,180,215,5.7)}" fill="none" stroke="{SEC}" stroke-width="13" stroke-linecap="round" opacity="0.28"/>')
    o.append(f'<line x1="{PX(200)}" y1="{PY(soffit(200))-58}" x2="{PX(198):.1f}" y2="{PY(soffit(198)+5.7):.1f}" stroke="{GR}" stroke-width="0.7" marker-end="url(#a)"/>')
    o.append(f'<text class="cal" x="{PX(202)}" y="{PY(soffit(200))-62}" fill="#1F8A70">traspasse ≥ lb,nec = 25,7 cm</text>')
    o.append(f'<line x1="{PX(120)}" y1="{PY(-H)+62}" x2="{PX(140):.1f}" y2="{PY(soffit(140)+8.5):.1f}" stroke="{GR}" stroke-width="0.7" marker-end="url(#a)"/>')
    o.append(f'<text class="cal" x="{PX(40)}" y="{PY(-H)+66}" fill="{AMB}">N2a · arranque do patamar</text>')
    o.append(f'<line x1="{PX(300)}" y1="{PY(soffit(280))-46}" x2="{PX(280):.1f}" y2="{PY(soffit(280)+3.0):.1f}" stroke="{GR}" stroke-width="0.7" marker-end="url(#a)"/>')
    o.append(f'<text class="cal" x="{PX(302)}" y="{PY(soffit(280))-50}" fill="{M}">N2b · barra do lance</text>')
    o.append(f'<text class="cal" x="{PX(40)}" y="{PY(-H)+94}" fill="{M}">N1 · principal do patamar</text>')
    o.append(f'<line x1="{PX(120)}" y1="{PY(-H)+90}" x2="{PX(100):.1f}" y2="{PY(-9.0):.1f}" stroke="{GR}" stroke-width="0.7" marker-end="url(#a)"/>')
    return o
build(0,360,-60,175,1100,60,ex_n2,"Divisão da N2 em arranque (N2a) e barra do lance (N2b)","n2_dividida")

# ---- canto reentrante ----
def ex_c(PX,PY,sc):
    o=[]
    o.append(f'<path d="{barpath(PX,PY,60,190,3.0)}" fill="none" stroke="{M}" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>')
    for x in (126,141):
        o.append(f'<circle cx="{PX(x):.1f}" cy="{PY(soffit(x)+6.5):.1f}" r="7" fill="#fff" stroke="{ANC}" stroke-width="3"/>')
    o.append(f'<line x1="{PX(124):.1f}" y1="{PY(soffit(124)+1):.1f}" x2="{PX(112):.1f}" y2="{PY(-34):.1f}" stroke="{M}" stroke-width="2.4" marker-end="url(#r)"/>')
    o.append(f'<text class="cal" x="{PX(118)}" y="{PY(-40)}" fill="{M}">resultante empurra o cobrimento para fora</text>')
    o.append(f'<line x1="{PX(134)}" y1="{PY(46)}" x2="{PX(134):.1f}" y2="{PY(soffit(134)+11):.1f}" stroke="{GR}" stroke-width="0.7" marker-end="url(#a)"/>')
    o.append(f'<text class="cal" x="{PX(138)}" y="{PY(48)}" fill="{ANC}">N6 · duas barras de ancoragem</text>')
    o.append(f'<text class="cal" x="{PX(52)}" y="{PY(-20)}" fill="{M}">armadura principal</text>')
    return o
build(55,235,-52,70,1000,55,ex_c,"Canto reentrante entre patamar e lance","canto")
print("ok")
