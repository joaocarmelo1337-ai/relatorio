"""O selo cinza é o padrão de quem não achou a cor.

Se uma cor de garantia ou de prioridade deixar de casar com a tabela do
estilo, a tela não quebra: ela fica cinza, e ninguém nota. Estes testes
existem para que isso quebre aqui, e não na banca.
"""

import unittest

from tcc import estilo
from tcc.services import garantias, gut


class TestCoresDosSelos(unittest.TestCase):
    def test_toda_prioridade_tem_cor_propria(self):
        classes = {
            prioridade: estilo.classe_da_cor(gut.PRIORIDADE_ROTULO[prioridade][2])
            for prioridade in (1, 2, 3)
        }
        self.assertEqual(classes, {1: "selo-vermelho", 2: "selo-amarelo",
                                   3: "selo-verde"})

    def test_toda_situacao_de_garantia_tem_cor(self):
        esperado = {
            garantias.VIGENTE: "selo-verde",
            garantias.VENCE_12: "selo-amarelo",
            garantias.VENCE_6: "selo-laranja",
            garantias.VENCIDA: "selo-vermelho",
            garantias.SEM_PRAZO: "selo-cinza",
        }
        for situacao, classe in esperado.items():
            cor = garantias.SITUACAO_VISUAL[situacao][1]
            self.assertEqual(estilo.classe_da_cor(cor), classe, f"situação {situacao}")

    def test_nenhuma_situacao_cai_no_cinza_por_engano(self):
        """Só SEM PRAZO pode ser cinza; as outras têm cor própria."""
        cinzas = [
            situacao for situacao, (_, cor) in garantias.SITUACAO_VISUAL.items()
            if estilo.classe_da_cor(cor) == "selo-cinza"
        ]
        self.assertEqual(cinzas, [garantias.SEM_PRAZO])

    def test_a_comparacao_ignora_caixa_e_espacos(self):
        self.assertEqual(estilo.classe_da_cor("#2E7D32"), "selo-verde")
        self.assertEqual(estilo.classe_da_cor("  #2e7d32  "), "selo-verde")

    def test_cor_desconhecida_vira_cinza_sem_quebrar(self):
        self.assertEqual(estilo.classe_da_cor("#123456"), "selo-cinza")
        self.assertEqual(estilo.classe_da_cor(None), "selo-cinza")

    def test_selo_devolve_html_com_a_classe(self):
        html = estilo.selo("VENCIDA", garantias.SITUACAO_VISUAL[garantias.VENCIDA][1])
        self.assertIn('class="selo selo-vermelho"', html)
        self.assertIn("VENCIDA", html)


if __name__ == "__main__":
    unittest.main()
