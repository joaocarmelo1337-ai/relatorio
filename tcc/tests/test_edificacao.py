import unittest
from datetime import date

from tcc.services import edificacao as ed


class TestIdade(unittest.TestCase):
    HABITE_SE = date(2024, 3, 15)

    def test_idade_do_exemplo_do_tcc(self):
        # Habite-se 15/03/2024, referencia 20/08/2026 -> 2 anos e 5 meses
        self.assertEqual(ed.idade(self.HABITE_SE, date(2026, 8, 20)), (2, 5))
        self.assertEqual(
            ed.idade_extenso(self.HABITE_SE, date(2026, 8, 20)),
            "2 anos e 5 meses",
        )

    def test_mes_so_conta_quando_o_dia_chega(self):
        self.assertEqual(ed.idade(self.HABITE_SE, date(2024, 4, 14)), (0, 0))
        self.assertEqual(ed.idade(self.HABITE_SE, date(2024, 4, 15)), (0, 1))

    def test_aniversario_exato(self):
        self.assertEqual(ed.idade(self.HABITE_SE, date(2027, 3, 15)), (3, 0))

    def test_texto_singular(self):
        self.assertEqual(ed.idade_extenso(self.HABITE_SE, date(2025, 4, 15)),
                         "1 ano e 1 mes")

    def test_sem_habite_se(self):
        self.assertIsNone(ed.idade(None))
        self.assertEqual(ed.idade_extenso(None), "Habite-se nao informado")

    def test_faixas(self):
        self.assertEqual(ed.faixa_etaria(self.HABITE_SE, date(2024, 9, 1)), "0-1 ano")
        self.assertEqual(ed.faixa_etaria(self.HABITE_SE, date(2025, 9, 1)), "1-2 anos")
        self.assertEqual(ed.faixa_etaria(self.HABITE_SE, date(2026, 9, 1)), "2-3 anos")
        self.assertEqual(ed.faixa_etaria(self.HABITE_SE, date(2027, 9, 1)), "mais de 3 anos")

    def test_recorte_de_ate_3_anos(self):
        self.assertTrue(ed.dentro_do_recorte(self.HABITE_SE, date(2027, 3, 14)))
        self.assertFalse(ed.dentro_do_recorte(self.HABITE_SE, date(2027, 3, 15)))

    def test_aceita_data_em_texto(self):
        self.assertEqual(ed.idade("2024-03-15", "2026-08-20"), (2, 5))


if __name__ == "__main__":
    unittest.main()
