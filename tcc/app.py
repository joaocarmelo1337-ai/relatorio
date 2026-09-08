"""JOAO CARMELO - TCC | Sistema de Vistoria, Garantias e Manutencao.

Casca da aplicacao Streamlit: login, navegacao lateral e as primeiras
paginas. A regra de negocio mora em tcc/services (testada sem Streamlit).

    streamlit run tcc/app.py
"""

from datetime import date, datetime

import streamlit as st

from tcc import config
from tcc.database import db, seed
from tcc.services import edificacao, garantias

st.set_page_config(
    page_title="João Carmelo — TCC",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------------------- infraestrutura
@st.cache_resource
def conexao():
    con = db.criar_banco()
    seed.semear_tudo(con)
    return con


def agora():
    return datetime.now().isoformat(timespec="seconds")


# ---------------------------------------------------------------------- login
def tela_login(con):
    _, meio, _ = st.columns([1, 2, 1])
    with meio:
        st.markdown(f"## {config.TITULO}")
        st.caption(config.SUBTITULO)
        with st.form("login"):
            usuario = st.text_input("Usuário", value="admin")
            senha = st.text_input("Senha", type="password")
            st.checkbox("Lembrar acesso", key="lembrar")
            entrou = st.form_submit_button("ENTRAR", use_container_width=True)
        if entrou:
            linha = con.execute(
                "SELECT * FROM usuarios WHERE usuario = ?", (usuario,)
            ).fetchone()
            if linha and seed.conferir_senha(senha, linha["senha_hash"], linha["salt"]):
                st.session_state["usuario"] = linha["nome"] or linha["usuario"]
                st.rerun()
            else:
                st.error("Usuário ou senha inválidos.")
        st.caption(f"_{config.LEMA}_")


# ------------------------------------------------------------------- paginas
def pagina_inicio(con):
    st.subheader("Visão geral")
    total_residencias = con.execute("SELECT COUNT(*) n FROM residencias").fetchone()["n"]
    total_vistorias = con.execute("SELECT COUNT(*) n FROM vistorias").fetchone()["n"]
    total_ocorrencias = con.execute(
        "SELECT COUNT(*) n FROM ocorrencias WHERE resultado = 'Nao Conforme'"
    ).fetchone()["n"]

    a, b, c = st.columns(3)
    a.metric("Residências cadastradas", total_residencias)
    b.metric("Vistorias realizadas", total_vistorias)
    c.metric("Manifestações encontradas", total_ocorrencias)

    if total_residencias == 0:
        st.info(
            "Nenhuma residência cadastrada ainda. Comece em **🏘 Residências**. "
            "Os cartões de prioridade, os gráficos e o relógio de garantias "
            "aparecem assim que houver dados."
        )
    st.caption(config.AVISO_RESPONSABILIDADE)


def pagina_residencias(con):
    st.subheader("Residências")

    with st.expander("➕ Cadastrar residência", expanded=False):
        with st.form("nova_residencia", clear_on_submit=True):
            col1, col2 = st.columns(2)
            nome = col1.text_input("Identificação da residência *")
            proprietario = col2.text_input("Proprietário")
            endereco = col1.text_input("Endereço")
            bairro = col2.text_input("Bairro")
            cidade = col1.text_input("Cidade", value="Campo Grande")
            uf = col2.text_input("UF", value="MS", max_chars=2)
            area = col1.number_input("Área construída (m²)", min_value=0.0, step=1.0)
            pavimentos = col2.number_input("Pavimentos", min_value=0, step=1)
            construtora = col1.text_input("Construtora")
            responsavel = col2.text_input("Responsável técnico")
            habite_se = col1.date_input(
                "Data do Habite-se", value=None, format="DD/MM/YYYY"
            )
            observacoes = st.text_area("Observações")
            salvou = st.form_submit_button("Salvar residência")

        if salvou:
            if not nome.strip():
                st.error("A identificação da residência é obrigatória.")
            else:
                con.execute(
                    "INSERT INTO residencias (nome, proprietario, endereco, bairro, "
                    "cidade, uf, area_construida, pavimentos, construtora, "
                    "responsavel_tecnico, data_habite_se, observacoes, criado_em) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        nome.strip(), proprietario, endereco, bairro, cidade, uf,
                        area or None, pavimentos or None, construtora, responsavel,
                        habite_se.isoformat() if habite_se else None,
                        observacoes, agora(),
                    ),
                )
                con.commit()
                st.success(f"Residência “{nome}” cadastrada.")
                st.rerun()

    linhas = con.execute(
        "SELECT * FROM residencias ORDER BY nome"
    ).fetchall()
    if not linhas:
        st.info("Nenhuma residência cadastrada.")
        return

    for linha in linhas:
        idade = edificacao.idade_extenso(linha["data_habite_se"])
        no_recorte = edificacao.dentro_do_recorte(linha["data_habite_se"])
        marca = "" if no_recorte else "  ·  fora do recorte de 3 anos"
        with st.container(border=True):
            st.markdown(f"**{linha['nome']}**")
            st.caption(
                f"Habite-se: {formatar_data(linha['data_habite_se'])}  ·  "
                f"Idade: {idade}{marca}"
            )


def pagina_configuracoes(con):
    st.subheader("Configurações")

    pendentes = seed.regras_pendentes_de_conferencia(con)
    if pendentes:
        st.warning(
            f"**{pendentes} prazos de garantia ainda não foram conferidos.** "
            "A tabela foi criada com as linhas da NBR 17170:2022 sem os valores "
            "preenchidos — nenhum prazo foi presumido. Preencha cada prazo com "
            "a norma na mão e marque como conferido; até lá, essas garantias "
            "aparecem como **⚪ SEM PRAZO TIPIFICADO**."
        )

    st.markdown("#### Prazos de garantia")
    regras = con.execute(
        "SELECT r.id, s.nome AS sistema, r.componente, r.tipo_falha, "
        "r.prazo_anos, r.fonte, r.conferido "
        "FROM regras_garantia r LEFT JOIN sistemas s ON s.id = r.sistema_id "
        "ORDER BY s.ordem, r.componente"
    ).fetchall()
    st.dataframe([dict(linha) for linha in regras], use_container_width=True)

    st.markdown("#### Sobre o TCC")
    st.write(
        f"**Acadêmico:** {config.ACADEMICO}  \n"
        f"**Curso:** {config.CURSO}  \n"
        f"**Instituição:** {config.INSTITUICAO}  \n"
        f"**Orientador:** {config.ORIENTADOR}  \n"
        f"**Ano:** {config.ANO}"
    )


def pagina_em_construcao(nome):
    st.subheader(nome)
    st.info(
        "Módulo previsto e ainda não implementado. A ordem de construção está "
        "no README, em “Ordem de trabalho”."
    )


def formatar_data(iso):
    if not iso:
        return "—"
    return date.fromisoformat(str(iso)[:10]).strftime("%d/%m/%Y")


# ---------------------------------------------------------------------- main
PAGINAS = {
    "Início": pagina_inicio,
    "Residências": pagina_residencias,
    "Configurações": pagina_configuracoes,
}


def main():
    con = conexao()

    if "usuario" not in st.session_state:
        tela_login(con)
        return

    with st.sidebar:
        st.markdown(f"### {config.TITULO}")
        st.caption(config.SUBTITULO)
        rotulos = [f"{icone} {nome}" for icone, nome in config.MENU]
        escolha = st.radio("Navegação", rotulos, label_visibility="collapsed")
        st.divider()
        st.caption(f"Sessão: {st.session_state['usuario']}")
        if st.button("Sair", use_container_width=True):
            del st.session_state["usuario"]
            st.rerun()

    nome_pagina = escolha.split(" ", 1)[1]
    st.markdown(f"# {nome_pagina}")
    PAGINAS.get(nome_pagina, lambda _: pagina_em_construcao(nome_pagina))(con)


if __name__ == "__main__":
    main()
