"""Sistema visual da plataforma.

Um lugar só para cor, tipografia, espaçamento e os componentes de tela
(cabeçalho, cartão de indicador, selo de status). As páginas montam a
interface com estas peças em vez de escreverem HTML solto — assim o
sistema inteiro muda de aparência editando este arquivo.
"""

import base64
from pathlib import Path

import streamlit as st
from streamlit_option_menu import option_menu

# --------------------------------------------------------------------- paleta
VERDE_FUNDO = "#163A28"      # barra lateral
VERDE_HOVER = "#1F4E35"
VERDE_ATIVO = "#24593D"
VERDE_ACAO = "#1C6B43"       # botão primário
VERDE_CLARO = "#E8F0EA"      # fundo de ícone
FUNDO = "#F6F7F5"
CARTAO = "#FFFFFF"
BORDA = "#E3E8E4"
TEXTO = "#1F2A24"
SUAVE = "#6B7A70"

VERDE = "#2E7D32"
AMARELO = "#E6A700"
LARANJA = "#E67E22"
VERMELHO = "#C0392B"
CINZA = "#7F8C8D"

CAPA = Path(__file__).resolve().parent / "assets" / "capa.jpg"


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Source+Serif+4:ital,wght@1,400&display=swap');

:root{
  --verde-fundo:#163A28; --verde-hover:#1F4E35; --verde-ativo:#24593D;
  --verde-acao:#1C6B43; --verde-claro:#E8F0EA;
  --fundo:#F6F7F5; --cartao:#FFFFFF; --borda:#E3E8E4;
  --texto:#1F2A24; --suave:#6B7A70;
  --raio:14px;
  --sombra:0 1px 2px rgba(22,58,40,.04), 0 4px 16px rgba(22,58,40,.05);
}

html, body, [class*="css"], .stApp{
  font-family:'Inter',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
  color:var(--texto);
}
.stApp{ background:var(--fundo); }
[data-testid="stHeader"]{ background:transparent; height:0; }
[data-testid="stToolbar"]{ display:none; }
#MainMenu, footer{ visibility:hidden; }
[data-testid="stMainBlockContainer"]{ padding:1.6rem 2.4rem 4rem; max-width:1480px; }

h1,h2,h3,h4{ font-family:'Inter',sans-serif; letter-spacing:-.02em; color:var(--texto); }
h1{ font-size:1.9rem; font-weight:700; }
h2{ font-size:1.35rem; font-weight:650; }
h3{ font-size:1.1rem; font-weight:600; }

/* ------------------------------------------------------- barra lateral */
[data-testid="stSidebar"]{
  background:var(--verde-fundo);
  border-right:none;
}
[data-testid="stSidebar"] *{ color:#DCE6DF; }
[data-testid="stSidebar"] [data-testid="stMainBlockContainer"],
[data-testid="stSidebarUserContent"]{ padding-top:1.1rem; }

.marca{ display:flex; gap:.8rem; align-items:flex-start; padding:.2rem .35rem 1.3rem; }
.marca-icone{
  width:46px; height:46px; flex:0 0 46px; border-radius:12px;
  border:1.6px solid rgba(220,230,223,.55);
  display:flex; align-items:center; justify-content:center;
}
.marca-nome{ font-size:.95rem; font-weight:700; color:#FFF; line-height:1.25;
  letter-spacing:.01em; }
.marca-sub{ font-size:.72rem; color:rgba(220,230,223,.72); line-height:1.35;
  margin-top:.25rem; }

/* O menu é um componente próprio (streamlit-option-menu); aqui ficam só
   os ajustes que o dicionário de estilos dele não alcança. */
[data-testid="stSidebar"] .nav-link-selected .icon{ color:#FFFFFF !important; }
[data-testid="stSidebar"] iframe{ border:none; background:transparent; }

.rodape-lateral{
  margin-top:1.4rem; padding:1.1rem .5rem 0; border-top:1px solid rgba(220,230,223,.16);
  font-size:.78rem; color:rgba(220,230,223,.6); line-height:1.6;
}
[data-testid="stSidebar"] .stButton button{
  background:transparent; border:1px solid rgba(220,230,223,.3); color:#DCE6DF;
  font-weight:500;
}
[data-testid="stSidebar"] .stButton button:hover{
  background:var(--verde-hover); border-color:rgba(220,230,223,.5); color:#FFF;
}

/* -------------------------------------------------------- cabeçalho */
.cabecalho{
  display:flex; align-items:center; justify-content:space-between; gap:1rem;
  padding-bottom:1rem; margin-bottom:1.1rem; border-bottom:1px solid var(--borda);
}
.cabecalho-pagina{ font-size:1.45rem; font-weight:700; letter-spacing:-.02em; }
.cabecalho-usuario{ display:flex; align-items:center; gap:.7rem;
  font-size:.86rem; color:var(--suave); }
.avatar{
  width:34px; height:34px; border-radius:50%; background:var(--verde-fundo);
  color:#FFF; display:flex; align-items:center; justify-content:center;
  font-size:.76rem; font-weight:700; letter-spacing:.03em;
}

/* ------------------------------------------------------------- capa */
.capa{
  position:relative; border-radius:var(--raio); overflow:hidden;
  padding:2.6rem 2.4rem; margin-bottom:1.1rem; min-height:230px;
  display:flex; flex-direction:column; justify-content:center;
  background:linear-gradient(115deg,#12301F 0%,#1B4830 52%,#256B45 100%);
  box-shadow:var(--sombra);
}
.capa.com-foto::after{
  content:""; position:absolute; inset:0;
  background:linear-gradient(100deg,rgba(18,48,31,.96) 0%,rgba(27,72,48,.86) 42%,rgba(27,72,48,.25) 100%);
}
.capa-conteudo{ position:relative; z-index:2; max-width:600px; }
.capa-etiqueta{
  font-size:.74rem; font-weight:600; letter-spacing:.16em; text-transform:uppercase;
  color:rgba(220,230,223,.82); line-height:1.7; margin-bottom:.7rem;
}
.capa h2{ font-size:2.35rem; font-weight:700; color:#FFF; margin:0 0 .7rem;
  line-height:1.12; letter-spacing:-.025em; }
.capa p{ font-size:.98rem; color:rgba(228,238,231,.9); margin:0; max-width:440px;
  line-height:1.6; }

/* --------------------------------------------------------- indicadores */
.indicadores{
  display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr));
  gap:.85rem; margin-bottom:1.1rem;
}
.indicador{
  background:var(--cartao); border:1px solid var(--borda); border-radius:var(--raio);
  padding:1.15rem 1.25rem; display:flex; align-items:center; gap:1rem;
  box-shadow:var(--sombra);
}
.indicador-icone{
  width:48px; height:48px; flex:0 0 48px; border-radius:12px;
  background:var(--verde-claro); display:flex; align-items:center;
  justify-content:center; font-size:1.35rem;
}
.indicador-valor{ font-size:1.75rem; font-weight:700; line-height:1;
  letter-spacing:-.03em; }
.indicador-rotulo{ font-size:.8rem; color:var(--suave); margin-top:.3rem;
  line-height:1.35; }

/* -------------------------------------------------------------- painel */
.painel{
  background:var(--cartao); border:1px solid var(--borda); border-radius:var(--raio);
  padding:1.5rem 1.7rem; box-shadow:var(--sombra); margin-bottom:1.1rem;
}
.painel h3{ margin:0 0 .55rem; }
.painel p{ color:var(--suave); font-size:.92rem; line-height:1.65; margin:0; }
.painel-duplo{ display:grid; grid-template-columns:1.5fr 1fr; gap:2.4rem;
  align-items:center; }
@media (max-width:900px){ .painel-duplo{ grid-template-columns:1fr; gap:1.4rem; } }
.citacao{
  font-family:'Source Serif 4',Georgia,serif; font-style:italic;
  font-size:1.02rem; color:var(--texto); line-height:1.65;
  border-left:2px solid var(--borda); padding-left:1.4rem;
}

/* --------------------------------------------------------------- selos */
.selo{
  display:inline-flex; align-items:center; gap:.4rem; font-size:.76rem;
  font-weight:600; padding:.26rem .62rem; border-radius:999px;
  border:1px solid transparent; white-space:nowrap;
}
.selo-verde   { background:#E9F4EA; color:#256B2C; border-color:#CDE6D1; }
.selo-amarelo { background:#FDF4DC; color:#8A6400; border-color:#F2E2B5; }
.selo-laranja { background:#FDEEE0; color:#9A5312; border-color:#F5DBC2; }
.selo-vermelho{ background:#FBEAE8; color:#96271C; border-color:#F2CFCB; }
.selo-cinza   { background:#F0F2F0; color:#5C6B62; border-color:#E0E5E1; }

/* ----------------------------------------------------------- controles */
.stButton button{
  border-radius:9px; font-weight:600; font-size:.88rem; padding:.5rem 1.15rem;
  border:1px solid var(--borda); background:var(--cartao); color:var(--texto);
  box-shadow:none; transition:all .14s ease;
}
.stButton button:hover{ border-color:#C3CFC7; background:#FAFBFA; color:var(--texto); }
.stButton button[kind="primary"], .stFormSubmitButton button[kind="primary"]{
  background:var(--verde-acao); border-color:var(--verde-acao); color:#FFF;
}
.stButton button[kind="primary"]:hover, .stFormSubmitButton button[kind="primary"]:hover{
  background:#175836; border-color:#175836; color:#FFF;
}
.stFormSubmitButton button{ border-radius:9px; font-weight:600; font-size:.88rem; }

[data-testid="stForm"]{
  background:var(--cartao); border:1px solid var(--borda);
  border-radius:var(--raio); padding:1.4rem 1.5rem; box-shadow:var(--sombra);
}
[data-testid="stExpander"]{
  background:var(--cartao); border:1px solid var(--borda) !important;
  border-radius:var(--raio) !important; box-shadow:var(--sombra); overflow:hidden;
}
[data-testid="stExpander"] summary{ font-weight:550; font-size:.92rem; padding:.85rem 1.1rem; }
[data-testid="stExpander"] summary:hover{ color:var(--verde-acao); }

[data-testid="stVerticalBlockBorderWrapper"] > div > [data-testid="stVerticalBlock"]{ gap:.6rem; }

input, textarea, .stSelectbox div[data-baseweb="select"] > div{
  border-radius:9px !important; border-color:var(--borda) !important;
  font-size:.9rem !important;
}
input:focus, textarea:focus{ border-color:var(--verde-acao) !important; }
label p{ font-size:.85rem !important; font-weight:550 !important; color:#3C4A42 !important; }

[data-testid="stDataFrame"]{ border-radius:var(--raio); overflow:hidden;
  border:1px solid var(--borda); }
hr{ border-color:var(--borda); margin:1.4rem 0; }
[data-testid="stCaptionContainer"] p{ font-size:.8rem; color:var(--suave); line-height:1.55; }

.rodape{
  margin-top:3rem; padding-top:1.2rem; border-top:1px solid var(--borda);
  display:flex; justify-content:space-between; flex-wrap:wrap; gap:1rem;
  font-size:.78rem; color:var(--suave);
}
.rodape strong{ color:var(--texto); font-weight:650; letter-spacing:.02em; }
</style>
"""


def aplicar():
    """Injeta o CSS. Chamar uma vez, no começo do app."""
    st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------- componentes
def marca(nome, subtitulo):
    """Identidade no topo da barra lateral."""
    casa = (
        '<svg width="26" height="26" viewBox="0 0 24 24" fill="none" '
        'stroke="#DCE6DF" stroke-width="1.6" stroke-linecap="round" '
        'stroke-linejoin="round"><path d="M3 10.5 12 3l9 7.5"/>'
        '<path d="M5 9.6V20a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9.6"/>'
        '<path d="M9.5 21v-5.5h5V21"/></svg>'
    )
    st.markdown(
        f'<div class="marca"><div class="marca-icone">{casa}</div>'
        f'<div><div class="marca-nome">{nome}</div>'
        f'<div class="marca-sub">{subtitulo}</div></div></div>',
        unsafe_allow_html=True,
    )


def menu_lateral(itens, chave="pagina"):
    """Navegação da barra lateral, com ícones de linha do Bootstrap Icons.

    A página escolhida fica em st.session_state[chave]. Quem decide é o
    estado, não o componente: assim a navegação pode ser conduzida de fora
    (por um botão de atalho, ou por um teste) e o menu acompanha.
    """
    nomes = [nome for _, nome in itens]
    icones = [icone for icone, _ in itens]
    atual = st.session_state.get(chave, nomes[0])
    indice = nomes.index(atual) if atual in nomes else 0

    escolhido = option_menu(
        menu_title=None,
        options=nomes,
        icons=icones,
        default_index=indice,
        key=f"menu_{chave}",
        styles={
            # O componente roda em iframe próprio, cujo documento tem fundo
            # claro por padrão. "transparent" deixaria o branco do iframe
            # aparecer; pintar do mesmo verde da lateral é o que funde os dois.
            "container": {"padding": "0", "background-color": VERDE_FUNDO,
                          "border-radius": "0"},
            "icon": {"color": "#9DB6A6", "font-size": "1rem"},
            "nav-link": {
                "font-family": "Inter, sans-serif", "font-size": "0.89rem",
                "font-weight": "500", "color": "#C2D3C8",
                "padding": "0.6rem 0.8rem", "margin": "0.08rem 0",
                "border-radius": "9px", "--hover-color": VERDE_HOVER,
                "text-align": "left",
            },
            "nav-link-selected": {
                "background-color": VERDE_ATIVO, "color": "#FFFFFF",
                "font-weight": "600",
            },
        },
    )
    st.session_state[chave] = escolhido
    return escolhido


def cabecalho(pagina, usuario):
    """Faixa superior: onde estou e quem sou."""
    iniciais = "".join(parte[0] for parte in usuario.split()[:2]).upper() or "?"
    st.markdown(
        f'<div class="cabecalho"><div class="cabecalho-pagina">{pagina}</div>'
        f'<div class="cabecalho-usuario"><span>Olá, {usuario}</span>'
        f'<div class="avatar">{iniciais}</div></div></div>',
        unsafe_allow_html=True,
    )


def capa(etiqueta, titulo, texto):
    """Faixa de abertura do painel inicial.

    Usa tcc/assets/capa.jpg como fundo quando o arquivo existir; sem ele,
    fica o degradê — que é uma escolha de desenho, não uma falta.
    """
    classe, estilo = "capa", ""
    if CAPA.exists():
        dados = base64.b64encode(CAPA.read_bytes()).decode()
        classe = "capa com-foto"
        estilo = (f' style="background-image:url(data:image/jpeg;base64,{dados});'
                  'background-size:cover;background-position:center"')
    st.markdown(
        f'<div class="{classe}"{estilo}><div class="capa-conteudo">'
        f'<div class="capa-etiqueta">{etiqueta}</div>'
        f'<h2>{titulo}</h2><p>{texto}</p></div></div>',
        unsafe_allow_html=True,
    )


def indicadores(itens):
    """Fileira de cartões. `itens` = [(ícone, valor, rótulo), ...]"""
    cartoes = "".join(
        f'<div class="indicador"><div class="indicador-icone">{icone}</div>'
        f'<div><div class="indicador-valor">{valor}</div>'
        f'<div class="indicador-rotulo">{rotulo}</div></div></div>'
        for icone, valor, rotulo in itens
    )
    st.markdown(f'<div class="indicadores">{cartoes}</div>', unsafe_allow_html=True)


def painel(titulo, texto=None, citacao=None):
    corpo = f"<h3>{titulo}</h3>"
    if texto:
        corpo += f"<p>{texto}</p>"
    if citacao:
        corpo = (f'<div class="painel-duplo"><div>{corpo}</div>'
                 f'<div class="citacao">{citacao}</div></div>')
    st.markdown(f'<div class="painel">{corpo}</div>', unsafe_allow_html=True)


# As cores chegam de garantias.py e gut.py escritas em minúsculas. Comparar
# sem normalizar deixava todo selo cinza.
CLASSE_DE_COR = {
    VERDE.lower(): "selo-verde", AMARELO.lower(): "selo-amarelo",
    LARANJA.lower(): "selo-laranja", VERMELHO.lower(): "selo-vermelho",
    CINZA.lower(): "selo-cinza",
}


def classe_da_cor(cor):
    return CLASSE_DE_COR.get(str(cor).strip().lower(), "selo-cinza")


def selo(texto, cor=CINZA):
    """Etiqueta de status (garantia, prioridade). Devolve HTML."""
    return f'<span class="selo {classe_da_cor(cor)}">{texto}</span>'


def rodape(titulo, subtitulo, palavras=()):
    direita = " &nbsp;|&nbsp; ".join(palavras)
    st.markdown(
        f'<div class="rodape"><div><strong>{titulo}</strong><br>{subtitulo}</div>'
        f'<div>{direita}</div></div>',
        unsafe_allow_html=True,
    )
