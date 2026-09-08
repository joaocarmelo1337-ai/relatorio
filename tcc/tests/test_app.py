"""Teste de fumaça da interface: o app sobe e todas as páginas renderizam.

Usa o AppTest do próprio Streamlit — executa o script de verdade, sem
navegador. Pulado quando o Streamlit não está instalado (os testes de
regra de negócio continuam rodando sem nenhuma dependência).
"""

import unittest
from pathlib import Path

try:
    from streamlit.testing.v1 import AppTest
    TEM_STREAMLIT = True
except ImportError:
    TEM_STREAMLIT = False

APP = str(Path(__file__).resolve().parent.parent / "app.py")


@unittest.skipUnless(TEM_STREAMLIT, "streamlit nao instalado")
class TestInterface(unittest.TestCase):
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
        self.assertEqual(17, len(at.radio[0].options))

    def test_todas_as_paginas_renderizam_sem_excecao(self):
        at = self.entrar()
        falhas = {}
        for opcao in at.radio[0].options:
            at.radio[0].set_value(opcao).run()
            erros = [e.value for e in at.exception]
            if erros:
                falhas[opcao] = erros[0]
        self.assertEqual({}, falhas)


if __name__ == "__main__":
    unittest.main()
