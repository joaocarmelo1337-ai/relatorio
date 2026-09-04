import cairosvg, os

C_MAIN="#D85A30"; C_SEC="#1D9E75"; C_ANC="#7F77DD"; C_GRAY="#888780"
C_TXT="#3d3d3a"; C_RED="#A32D2D"; C_AMB="#BA7517"

def svg(body,w,h):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>text{{font-family:Helvetica,Arial,sans-serif;font-size:13px;fill:{C_TXT}}} .s{{font-size:12px}} .b{{font-weight:600}}</style><rect width="{w}" height="{h}" fill="#ffffff"/>{body}</svg>'

figs={}

# 2 - dominios
figs["dominios"]=svg(f'''
<rect x="30" y="60" width="130" height="46" rx="5" fill="#E1F5EE" stroke="#0F6E56" stroke-width="1"/>
<rect x="160" y="60" width="95" height="46" rx="5" fill="#EAF3DE" stroke="#3B6D11" stroke-width="1"/>
<rect x="255" y="60" width="275" height="46" rx="5" fill="#FCEBEB" stroke="#A32D2D" stroke-width="1"/>
<text class="b" x="95" y="80" text-anchor="middle" fill="#0F6E56">Dominio 2</text>
<text class="s" x="95" y="97" text-anchor="middle" fill="#0F6E56">muito ductil</text>
<text class="b" x="207" y="80" text-anchor="middle" fill="#3B6D11">Dominio 3</text>
<text class="s" x="207" y="97" text-anchor="middle" fill="#3B6D11">faixa ideal</text>
<text class="b" x="392" y="80" text-anchor="middle" fill="#A32D2D">Dominio 4</text>
<text class="s" x="392" y="97" text-anchor="middle" fill="#A32D2D">ruptura fragil - nao usar</text>
<line x1="30" y1="118" x2="530" y2="118" stroke="{C_GRAY}"/>
<text class="s" x="30" y="136" text-anchor="middle">0</text>
<text class="s" x="160" y="136" text-anchor="middle">0,259</text>
<text class="s" x="255" y="136" text-anchor="middle">0,45</text>
<text class="s" x="530" y="136" text-anchor="middle">1,0</text>
<text class="s" x="280" y="158" text-anchor="middle">Kx = x / d</text>
<line x1="255" y1="38" x2="255" y2="56" stroke="{C_RED}" stroke-width="2"/>
<text class="s" x="255" y="30" text-anchor="middle" fill="{C_RED}">limite ductil (fck menor ou igual a 50 MPa)</text>
<line x1="200" y1="200" x2="200" y2="180" stroke="{C_SEC}" stroke-width="2"/>
<text class="s" x="200" y="216" text-anchor="middle" fill="#0F6E56">exemplo da apostila: Kx = 0,407</text>
''',560,235)

# 3 - opcoes principal
figs["opcoes_principal"]=svg(f'''
<text class="b" x="30" y="30">Opcao A - ganchos em 90 graus nas duas pontas</text>
<path d="M 40 66 L 40 48 L 500 48 L 500 66" fill="none" stroke="{C_MAIN}" stroke-width="3.5" stroke-linecap="round"/>
<text class="s" x="40" y="88">usar quando falta comprimento para ancorar reto</text>
<text class="b" x="30" y="140">Opcao B - reta, sem gancho</text>
<path d="M 40 160 L 500 160" fill="none" stroke="{C_MAIN}" stroke-width="3.5" stroke-linecap="round"/>
<text class="s" x="40" y="184">usar quando ha espaco para o lb,nec inteiro</text>
<text class="b" x="30" y="236">Opcao C - levantada (cavalete)</text>
<path d="M 40 268 L 180 268 L 280 240 L 500 240" fill="none" stroke="{C_MAIN}" stroke-width="3.5" stroke-linecap="round"/>
<text class="s" x="40" y="292">usar quando o momento inverte de sinal na dobra</text>
''',560,310)

# 4 - anatomia
figs["anatomia"]=svg(f'''
<line x1="90" y1="48" x2="460" y2="48" stroke="{C_GRAY}"/>
<line x1="90" y1="40" x2="90" y2="56" stroke="{C_GRAY}"/>
<line x1="460" y1="40" x2="460" y2="56" stroke="{C_GRAY}"/>
<text class="s" x="275" y="34" text-anchor="middle">trecho reto (vao livre e/ou ancoragem lb,nec)</text>
<path d="M 90 150 L 90 90 L 460 90" fill="none" stroke="{C_MAIN}" stroke-width="3.5" stroke-linecap="round"/>
<line x1="66" y1="90" x2="66" y2="150" stroke="{C_GRAY}"/>
<line x1="58" y1="90" x2="74" y2="90" stroke="{C_GRAY}"/>
<line x1="58" y1="150" x2="74" y2="150" stroke="{C_GRAY}"/>
<text class="s" x="86" y="172">gancho: dlg = h - 2c</text>
<text class="s" x="90" y="204">Comprimento total da barra = trecho reto + gancho (medido no eixo da barra)</text>
''',560,225)

# 5 - opcoes secundaria/borda
figs["opcoes_secundaria"]=svg(f'''
<text class="b" x="30" y="28">Distribuicao - opcao A - barra reta</text>
<path d="M 40 52 L 510 52" fill="none" stroke="{C_SEC}" stroke-width="3.5" stroke-linecap="round"/>
<text class="s" x="40" y="74">mais simples de executar</text>
<text class="b" x="30" y="122">Distribuicao - opcao B - ganchos nas pontas</text>
<path d="M 40 164 L 40 146 L 510 146 L 510 164" fill="none" stroke="{C_SEC}" stroke-width="3.5" stroke-linecap="round"/>
<text class="s" x="40" y="186">melhor ancoragem junto a bordas livres</text>
<text class="b" x="30" y="234">Borda - opcao A - em L</text>
<path d="M 40 276 L 40 258 L 380 258" fill="none" stroke="{C_ANC}" stroke-width="3.5" stroke-linecap="round"/>
<text class="s" x="40" y="298">gancho no apoio, ponta livre dentro da laje</text>
<text class="b" x="30" y="346">Borda - opcao B - grampo em U</text>
<path d="M 460 372 L 60 372 L 60 400 L 460 400" fill="none" stroke="{C_ANC}" stroke-width="3.5" stroke-linecap="round"/>
<text class="s" x="40" y="424">abraca as duas faces - melhor contra fissura de canto</text>
''',560,440)

# 6 - formatos N1..N6
figs["formatos_n"]=svg(f'''
<text class="b" x="30" y="26">N1 - principal do patamar - 1 gancho</text>
<path d="M 40 62 L 40 44 L 330 44" fill="none" stroke="{C_MAIN}" stroke-width="3.5" stroke-linecap="round"/>
<text class="b" x="30" y="112">N2 - principal do lance - 1 gancho</text>
<path d="M 40 130 L 480 130 L 480 148" fill="none" stroke="{C_MAIN}" stroke-width="3.5" stroke-linecap="round"/>
<text class="b" x="30" y="198">N3 - principal do lance superior - 2 ganchos</text>
<path d="M 40 234 L 40 216 L 400 216 L 400 234" fill="none" stroke="{C_MAIN}" stroke-width="3.5" stroke-linecap="round"/>
<text class="b" x="30" y="284">N4 - distribuicao - reta</text>
<path d="M 40 302 L 510 302" fill="none" stroke="{C_SEC}" stroke-width="3.5" stroke-linecap="round"/>
<text class="b" x="30" y="352">N5 - reforco da divisa - reta</text>
<path d="M 40 370 L 510 370" fill="none" stroke="{C_MAIN}" stroke-width="3.5" stroke-linecap="round"/>
<text class="b" x="30" y="420">N6 - ancoragem dos cantos - reta</text>
<path d="M 40 438 L 510 438" fill="none" stroke="{C_ANC}" stroke-width="3.5" stroke-linecap="round"/>
''',560,460)

# 7 - corte conjunto
figs["corte_conjunto"]=svg(f'''
<path d="M 40 250 L 170 250 L 400 120 L 520 120" fill="none" stroke="{C_GRAY}" stroke-width="1.2"/>
<path d="M 40 276 L 170 276 L 400 146 L 520 146" fill="none" stroke="{C_GRAY}" stroke-width="1.2"/>
<line x1="40" y1="250" x2="40" y2="276" stroke="{C_GRAY}" stroke-width="1.2"/>
<line x1="520" y1="120" x2="520" y2="146" stroke="{C_GRAY}" stroke-width="1.2"/>
<path d="M 56 244 L 56 266 L 175 266" fill="none" stroke="{C_MAIN}" stroke-width="3"/>
<text class="s" x="58" y="296" fill="{C_MAIN}">N1</text>
<path d="M 140 266 L 392 124 L 392 144" fill="none" stroke="{C_MAIN}" stroke-width="3"/>
<text class="s" x="270" y="216" fill="{C_MAIN}">N2</text>
<path d="M 250 176 L 250 196 L 470 128 L 500 128" fill="none" stroke="{C_MAIN}" stroke-width="3"/>
<text class="s" x="360" y="164" fill="{C_MAIN}">N3</text>
<circle cx="100" cy="266" r="4.5" fill="{C_SEC}"/>
<circle cx="230" cy="228" r="4.5" fill="{C_SEC}"/>
<circle cx="320" cy="177" r="4.5" fill="{C_SEC}"/>
<circle cx="450" cy="136" r="4.5" fill="{C_SEC}"/>
<text class="s" x="94" y="300" fill="#0F6E56">N4</text>
<circle cx="150" cy="266" r="4.5" fill="{C_MAIN}"/>
<text class="s" x="144" y="322" fill="{C_MAIN}">N5</text>
<circle cx="163" cy="262" r="5.5" fill="none" stroke="{C_ANC}" stroke-width="2.5"/>
<circle cx="184" cy="253" r="5.5" fill="none" stroke="{C_ANC}" stroke-width="2.5"/>
<circle cx="386" cy="132" r="5.5" fill="none" stroke="{C_ANC}" stroke-width="2.5"/>
<circle cx="408" cy="130" r="5.5" fill="none" stroke="{C_ANC}" stroke-width="2.5"/>
<line x1="176" y1="242" x2="176" y2="70" stroke="{C_GRAY}" stroke-dasharray="4 4"/>
<line x1="398" y1="120" x2="398" y2="70" stroke="{C_GRAY}" stroke-dasharray="4 4"/>
<text class="s" x="176" y="60" text-anchor="middle" fill="#3C3489">N6 - canto inferior</text>
<text class="s" x="420" y="60" text-anchor="middle" fill="#3C3489">N6 - canto superior</text>
''',560,340)

# 8 - N2 dividida
figs["n2_dividida"]=svg(f'''
<path d="M 40 230 L 165 230 L 400 105 L 520 105" fill="none" stroke="{C_GRAY}" stroke-width="1.2"/>
<path d="M 40 256 L 165 256 L 400 131 L 520 131" fill="none" stroke="{C_GRAY}" stroke-width="1.2"/>
<line x1="40" y1="230" x2="40" y2="256" stroke="{C_GRAY}" stroke-width="1.2"/>
<path d="M 56 224 L 56 246 L 160 246" fill="none" stroke="{C_MAIN}" stroke-width="3"/>
<text class="s" x="58" y="278" fill="{C_MAIN}">N1</text>
<path d="M 130 246 L 285 164" fill="none" stroke="{C_AMB}" stroke-width="3.5" stroke-linecap="round"/>
<text class="s" x="120" y="200" fill="{C_AMB}">N2a - arranque</text>
<path d="M 235 190 L 392 108 L 392 128" fill="none" stroke="{C_MAIN}" stroke-width="3.5" stroke-linecap="round"/>
<text class="s" x="330" y="152" fill="{C_MAIN}">N2b - lance</text>
<line x1="235" y1="190" x2="285" y2="164" stroke="{C_SEC}" stroke-width="9" stroke-linecap="round" opacity="0.3"/>
<line x1="260" y1="177" x2="300" y2="90" stroke="{C_GRAY}" stroke-dasharray="4 4"/>
<text class="s" x="306" y="82" fill="#0F6E56">traspasse maior ou igual a lb,nec = 25,7 cm</text>
''',560,300)

# 9 - vista principais
lines="".join(f'<line x1="{110+i*20}" y1="60" x2="{110+i*20}" y2="290" stroke="{C_MAIN}" stroke-width="2.6"/>' for i in range(16))
figs["vista_principais"]=svg(f'''
<rect x="100" y="52" width="330" height="246" fill="none" stroke="{C_GRAY}" stroke-dasharray="5 5"/>
{lines}
<text class="s" x="265" y="36" text-anchor="middle">sentido da subida (vertical)</text>
<text class="s" x="265" y="326" text-anchor="middle">16 barras Ø10 c/ 7,5 cm - largura do lance 121 cm</text>
''',560,345)

# 10 - vista secundarias
lines2="".join(f'<line x1="110" y1="{62+i*16}" x2="420" y2="{62+i*16}" stroke="{C_SEC}" stroke-width="2.6"/>' for i in range(15))
figs["vista_secundarias"]=svg(f'''
<rect x="100" y="52" width="330" height="246" fill="none" stroke="{C_GRAY}" stroke-dasharray="5 5"/>
{lines2}
<text class="s" x="265" y="36" text-anchor="middle">sentido da subida (vertical)</text>
<text class="s" x="265" y="326" text-anchor="middle">15 barras Ø6,3 c/ 15 cm - atravessam a largura</text>
''',560,345)

# 11 - canto reentrante
figs["canto"]=svg(f'''
<path d="M 40 190 L 175 190 L 400 60 L 520 60" fill="none" stroke="{C_GRAY}" stroke-width="1.2"/>
<path d="M 40 216 L 175 216 L 400 86 L 520 86" fill="none" stroke="{C_GRAY}" stroke-width="1.2"/>
<line x1="40" y1="190" x2="40" y2="216" stroke="{C_GRAY}" stroke-width="1.2"/>
<path d="M 60 208 L 178 208 L 396 82" fill="none" stroke="{C_MAIN}" stroke-width="3.5" stroke-linecap="round"/>
<text class="s" x="70" y="238" fill="{C_MAIN}">armadura principal</text>
<line x1="178" y1="216" x2="200" y2="268" stroke="{C_RED}" stroke-width="2"/>
<polygon points="200,272 194,258 206,258" fill="{C_RED}"/>
<text class="s" x="212" y="278" fill="{C_RED}">resultante empurra o concreto para fora</text>
<circle cx="163" cy="207" r="6" fill="none" stroke="{C_ANC}" stroke-width="2.5"/>
<circle cx="196" cy="196" r="6" fill="none" stroke="{C_ANC}" stroke-width="2.5"/>
<line x1="180" y1="180" x2="180" y2="140" stroke="{C_GRAY}" stroke-dasharray="4 4"/>
<text class="s" x="180" y="130" text-anchor="middle" fill="#3C3489">N6 - duas barras de ancoragem</text>
''',560,295)

for name,s in figs.items():
    open(f"fig/{name}.svg","w").write(s)
    cairosvg.svg2png(bytestring=s.encode(), write_to=f"fig/{name}.png", scale=2.0)
print("ok", len(figs))
