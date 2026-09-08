"""Teste de fumaça da interface: o app sobe e todas as páginas renderizam.

Usa o AppTest do próprio Streamlit — executa o script de verdade, sem
navegador. Pulado quando o Streamlit não está instalado (os testes de
regra de negócio continuam rodando sem nenhuma dependência).
"""

import tempfile
import unittest
from pathlib import Path

from tcc import config
from tcc.database import db, seed
from tcc.services import ambientes, vistorias

PAGINAS = [nome for _, nome in config.MENU]

try:
    from streamlit.testing.v1 import AppTest
    TEM_STREAMLIT = True
except ImportError:
    TEM_STREAMLIT = False

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def ir_para(teste, pagina):
    """Navega pelo estado, não pelo widget.

    O menu é um componente de terceiros e o AppTest não consegue clicar
    nele. Como a página escolhida vive em session_state['pagina'] e o menu
    apenas acompanha esse estado, o teste conduz a navegação por ali.
    """
    teste.session_state["pagina"] = pagina
    teste.run()
    return teste


def percorrer_paginas(teste):
    """Abre todas as páginas do menu. Devolve {página: problema} do que falhar.

    Não basta não estourar exceção: se toda página caísse no painel de
    "em construção", um teste que só olha exceções passaria igual. Por isso
    exige-se também que o cabeçalho nomeie a página aberta.
    """
    falhas = {}
    for pagina in PAGINAS:
        ir_para(teste, pagina)
        erros = [e.value for e in teste.exception]
        if erros:
            falhas[pagina] = f"exceção: {erros[0]}"
            continue
        tela = " ".join(str(elemento.value) for elemento in teste.markdown)
        if f'class="cabecalho-pagina">{pagina}<' not in tela:
            falhas[pagina] = "o cabeçalho não nomeia esta página"
    return falhas


@unittest.skipUnless(TEM_STREAMLIT, "streamlit nao instalado")
class TestInterface(unittest.TestCase):
    def setUp(self):
        import streamlit as st
        st.cache_resource.clear()

    def abrir(self):
        at = AppTest.from_file(APP, default_timeout=60)
        at.run()
        return at

    def entrar(self):
        at = self.abrir()
        at.text_input[0].set_value("admin")
        at.text_input[1].set_value("admin")
        at.button[0].click().run()
        return at

    def test_tela_de_login_aparece_primeiro(self):
        at = self.abrir()
        self.assertEqual([], [e.value for e in at.exception])
        self.assertEqual(["Usuário", "Senha"], [i.label for i in at.text_input])
        self.assertEqual(["ENTRAR"], [b.label for b in at.button])

    def test_senha_errada_nao_entra(self):
        at = self.abrir()
        at.text_input[0].set_value("admin")
        at.text_input[1].set_value("errada")
        at.button[0].click().run()
        self.assertTrue(at.error, "deveria mostrar erro de credencial")
        self.assertNotIn("usuario", at.session_state)

    def test_login_valido_abre_a_navegacao(self):
        at = self.entrar()
        self.assertEqual([], [e.value for e in at.exception])
        self.assertIn("usuario", at.session_state)
        self.assertEqual(17, len(PAGINAS))
        # sem escolha anterior, o menu abre no início
        self.assertEqual(at.session_state["pagina"], "Início")

    def test_todas_as_paginas_abrem_e_se_identificam(self):
        at = self.entrar()
        self.assertEqual({}, percorrer_paginas(at))

    def test_as_paginas_construidas_nao_caem_no_em_construcao(self):
        """As sete já entregues precisam mostrar conteúdo próprio."""
        at = self.entrar()
        prontas = ["Início", "Residências", "Ambientes", "Vistorias",
                   "Patologias", "Excel / Banco de Dados", "Configurações"]
        caiu = []
        for pagina in prontas:
            ir_para(at, pagina)
            tela = " ".join(str(elemento.value) for elemento in at.markdown)
            if "Módulo em construção" in tela:
                caiu.append(pagina)
        self.assertEqual([], caiu)


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(TEM_STREAMLIT, "streamlit nao instalado")
class TestInterfaceComDados(unittest.TestCase):
    """As páginas com o banco vazio só exercitam o estado 'nada cadastrado'.

    Aqui o banco tem residência, ambiente, vistoria e manifestação
    classificada, então os seletores, os expanders e o alerta de garantia
    são de fato renderizados.
    """

    def setUp(self):
        # O @st.cache_resource guarda a conexao entre execucoes do AppTest no
        # mesmo processo. Sem limpar, o app continuaria lendo o banco de um
        # teste anterior e este aqui nao estaria testando nada.
        import streamlit as st
        st.cache_resource.clear()

        self.tmp = tempfile.TemporaryDirectory()
        self.caminho_original = db.CAMINHO_BANCO
        db.CAMINHO_BANCO = Path(self.tmp.name) / "interface.db"

        con = db.criar_banco()
        seed.semear_tudo(con)
        rid = con.execute(
            "INSERT INTO residencias (nome, data_habite_se, data_protocolo, "
            "regime_normativo, criado_em) VALUES (?,?,?,?,?)",
            ("Casa Silva", "2024-03-15", "2024-01-10", "NBR 17170:2022", "2026-09-08"),
        ).lastrowid
        ambiente_id = ambientes.criar(con, rid, "Banheiro social")
        vistoria_id = vistorias.criar_vistoria(con, rid, "2026-09-08", "João Carmelo")

        item_id = con.execute(
            "SELECT id FROM itens_catalogo WHERE id_item = 'IT-006'"
        ).fetchone()["id"]          # muro, 3 anos -> garantia perto do fim
        ocorrencia_id = vistorias.registrar(
            con, vistoria_id, item_id, vistorias.NAO_CONFORME,
            ambiente_id=ambiente_id, descricao="Fissura no muro de divisa",
            origens=["Anomalia endógena"],
        )
        vistorias.classificar(con, ocorrencia_id, 6, 6, 6, "Fissura estabilizada")

        # uma segunda, sem classificação, para exercitar o aviso de pendência
        vistorias.registrar(
            con, vistoria_id,
            con.execute("SELECT id FROM itens_catalogo WHERE id_item = 'T3-04'").fetchone()["id"],
            vistorias.NAO_CONFORME, ambiente_id=ambiente_id, descricao="Lascamento",
        )
        con.commit()
        con.close()

    def tearDown(self):
        import streamlit as st
        st.cache_resource.clear()
        db.CAMINHO_BANCO = self.caminho_original
        self.tmp.cleanup()

    def test_todas_as_paginas_renderizam_com_dados(self):
        at = AppTest.from_file(APP, default_timeout=90)
        at.run()
        at.text_input[0].set_value("admin")
        at.text_input[1].set_value("admin")
        at.button[0].click().run()

        self.assertEqual({}, percorrer_paginas(at))

    def test_a_pagina_de_patologias_mostra_o_alerta_de_garantia(self):
        at = AppTest.from_file(APP, default_timeout=90)
        at.run()
        at.text_input[0].set_value("admin")
        at.text_input[1].set_value("admin")
        at.button[0].click().run()
        ir_para(at, "Patologias")

        self.assertEqual([], [e.value for e in at.exception])
        texto = " ".join(str(elemento.value) for elemento in at.error)
        self.assertIn("ALERTA DE GARANTIA", texto)
        pendentes = " ".join(str(elemento.value) for elemento in at.warning)
        self.assertIn("sem classificação GUT", pendentes)
