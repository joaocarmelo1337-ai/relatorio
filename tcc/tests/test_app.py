"""Teste de fumaça da interface: o app sobe e todas as páginas renderizam.

Usa o AppTest do próprio Streamlit — executa o script de verdade, sem
navegador. Pulado quando o Streamlit não está instalado (os testes de
regra de negócio continuam rodando sem nenhuma dependência).
"""

import tempfile
import unittest
from pathlib import Path

from tcc.database import db, seed
from tcc.services import ambientes, vistorias

try:
    from streamlit.testing.v1 import AppTest
    TEM_STREAMLIT = True
except ImportError:
    TEM_STREAMLIT = False

APP = str(Path(__file__).resolve().parent.parent / "app.py")


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
        self.assertEqual(17, len(at.radio(key="navegacao").options))

    def test_todas_as_paginas_renderizam_sem_excecao(self):
        at = self.entrar()
        falhas = {}
        for opcao in at.radio(key="navegacao").options:
            at.radio(key="navegacao").set_value(opcao).run()
            erros = [e.value for e in at.exception]
            if erros:
                falhas[opcao] = erros[0]
        self.assertEqual({}, falhas)


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

        falhas = {}
        for opcao in at.radio(key="navegacao").options:
            at.radio(key="navegacao").set_value(opcao).run()
            erros = [e.value for e in at.exception]
            if erros:
                falhas[opcao] = erros[0]
        self.assertEqual({}, falhas)

    def test_a_pagina_de_patologias_mostra_o_alerta_de_garantia(self):
        at = AppTest.from_file(APP, default_timeout=90)
        at.run()
        at.text_input[0].set_value("admin")
        at.text_input[1].set_value("admin")
        at.button[0].click().run()
        navegacao = at.radio(key="navegacao")
        patologias = next(o for o in navegacao.options if o.endswith("Patologias"))
        navegacao.set_value(patologias).run()

        self.assertEqual([], [e.value for e in at.exception])
        texto = " ".join(str(elemento.value) for elemento in at.error)
        self.assertIn("ALERTA DE GARANTIA", texto)
        pendentes = " ".join(str(elemento.value) for elemento in at.warning)
        self.assertIn("sem classificação GUT", pendentes)
