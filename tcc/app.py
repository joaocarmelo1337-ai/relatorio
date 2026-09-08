"""JOAO CARMELO - TCC | Sistema de Vistoria, Garantias e Manutencao.

Casca da aplicacao Streamlit: login, navegacao lateral e as primeiras
paginas. A regra de negocio mora em tcc/services (testada sem Streamlit).

    streamlit run tcc/app.py
"""

from datetime import date, datetime

import streamlit as st

from tcc import config
from tcc.database import db, seed
from tcc.services import importacao_excel
from tcc.services import edificacao, garantias, regime

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
            entrou = st.form_submit_button("ENTRAR", width="stretch")
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
                "Data do Habite-se", value=None, format="DD/MM/YYYY",
                help="Inicia a contagem dos prazos de garantia (NBR 17170, item 5).",
            )
            protocolo = col2.date_input(
                "Data de protocolo do projeto", value=None, format="DD/MM/YYYY",
                help="Define o regime normativo aplicável. Não confundir com o Habite-se.",
            )
            if protocolo:
                st.caption(f"Regime normativo: **{regime.regime_normativo(protocolo)}**")
            observacoes = st.text_area("Observações")
            salvou = st.form_submit_button("Salvar residência")

        if salvou:
            if not nome.strip():
                st.error("A identificação da residência é obrigatória.")
            else:
                protocolo_iso = protocolo.isoformat() if protocolo else None
                con.execute(
                    "INSERT INTO residencias (nome, proprietario, endereco, bairro, "
                    "cidade, uf, area_construida, pavimentos, construtora, "
                    "responsavel_tecnico, data_habite_se, data_protocolo, "
                    "regime_normativo, observacoes, criado_em) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        nome.strip(), proprietario, endereco, bairro, cidade, uf,
                        area or None, pavimentos or None, construtora, responsavel,
                        habite_se.isoformat() if habite_se else None,
                        protocolo_iso, regime.regime_normativo(protocolo_iso),
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
                f"Idade: {idade}{marca}  ·  "
                f"Regime: {linha['regime_normativo'] or '—'}"
            )


def pagina_excel(con):
    st.subheader("Excel / Banco de Dados")
    st.write(
        "A planilha do TCC é a fonte inicial dos dados. Importar de novo uma "
        "versão atualizada **atualiza** os registros pelo `ID_Obra`, `ID_Item` "
        "e `ID_Lancamento` — não duplica."
    )

    arquivo = st.file_uploader(
        "Planilha do TCC (.xlsx)", type=["xlsx"],
        help="Checklist_Vistoria_Garantias_TCC.xlsx",
    )
    if arquivo and st.button("IMPORTAR EXCEL", type="primary"):
        destino = config.UPLOADS / "planilha"
        destino.mkdir(parents=True, exist_ok=True)
        caminho = destino / arquivo.name
        caminho.write_bytes(arquivo.getbuffer())
        try:
            resumo = importacao_excel.importar(con, caminho)
        except importacao_excel.PlanilhaInvalida as erro:
            st.error(f"Planilha não reconhecida: {erro}")
        else:
            st.success(
                f"{resumo['itens_catalogo']} itens de catálogo · "
                f"{resumo['residencias']} residências · "
                f"{resumo['ocorrencias']} ocorrências."
            )
            if resumo["lancamentos_ignorados"]:
                st.warning(
                    "Lançamentos ignorados por apontarem para obra ou item "
                    f"inexistente: {', '.join(resumo['lancamentos_ignorados'])}"
                )

    st.divider()
    st.markdown("#### Catálogo de itens de verificação")
    itens = con.execute(
        "SELECT i.id_item, COALESCE(s.nome, i.sistema_texto) AS sistema, i.item, "
        "i.prazo_anos, i.tipo_falha_nbr, i.procedencia "
        "FROM itens_catalogo i LEFT JOIN sistemas s ON s.id = i.sistema_id "
        "ORDER BY i.id_item"
    ).fetchall()
    st.caption(f"{len(itens)} itens carregados.")
    st.dataframe([dict(linha) for linha in itens], width="stretch")


def pagina_configuracoes(con):
    st.subheader("Configurações")

    sem_prazo = seed.itens_sem_prazo(con)
    st.info(
        f"**{sem_prazo} itens do catálogo não têm prazo de garantia em anos.** "
        "Isso não é lacuna: são os 16 itens da Tabela 3 da NBR 17170 — cuja "
        "identificação é devida no ato da entrega, sem prazo em anos — e os "
        "itens que decorrem de manutenção do usuário. Aparecem como "
        "**⚪ SEM PRAZO TIPIFICADO** no relógio de garantias."
    )

    st.markdown("#### Síntese dos prazos — ABNT NBR 17170:2022")
    st.caption(
        "Síntese de apoio, por patamar de prazo. **Não substitui a norma**: a "
        "Tabela 2 da NBR 17170 contém 182 itens e deve ser consultada no texto "
        "oficial da ABNT antes de qualquer citação."
    )
    regras = con.execute(
        "SELECT prazo_texto AS prazo, componente, tipo_falha "
        "FROM regras_garantia ORDER BY prazo_anos DESC, componente"
    ).fetchall()
    st.dataframe([dict(linha) for linha in regras], width="stretch")

    st.markdown("#### Regime normativo")
    st.caption(
        f"Projeto protocolado **depois de {regime.LIMITE.strftime('%d/%m/%Y')}** "
        f"→ {regime.NBR_17170}. Até essa data → {regime.ANTERIOR}, que previa "
        "prazos de 2 anos, extintos pela NBR 17170. O limite é a publicação da "
        "norma (12/12/2022) somada aos 180 dias de vacância."
    )

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
    "Excel / Banco de Dados": pagina_excel,
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
        if st.button("Sair", width="stretch"):
            del st.session_state["usuario"]
            st.rerun()

    nome_pagina = escolha.split(" ", 1)[1]
    st.markdown(f"# {nome_pagina}")
    PAGINAS.get(nome_pagina, lambda _: pagina_em_construcao(nome_pagina))(con)


if __name__ == "__main__":
    main()
