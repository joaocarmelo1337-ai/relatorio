import unittest
from datetime import date

from tcc.services import garantias as g


class TestSomaDeMeses(unittest.TestCase):
    def test_soma_simples(self):
        self.assertEqual(g.somar_meses(date(2024, 3, 15), 12), date(2025, 3, 15))

    def test_ajusta_fim_de_mes(self):
        self.assertEqual(g.somar_meses(date(2024, 1, 31), 1), date(2024, 2, 29))
        self.assertEqual(g.somar_meses(date(2025, 1, 31), 1), date(2025, 2, 28))

    def test_29_de_fevereiro_em_ano_comum(self):
        self.assertEqual(g.somar_meses(date(2024, 2, 29), 12), date(2025, 2, 28))

    def test_virada_de_ano(self):
        self.assertEqual(g.somar_meses(date(2024, 11, 10), 3), date(2025, 2, 10))


class TestVencimento(unittest.TestCase):
    HABITE_SE = date(2024, 3, 15)

    def test_exemplo_da_impermeabilizacao(self):
        # Habite-se 15/03/2024 + 5 anos -> 15/03/2029 (exemplo do TCC)
        self.assertEqual(g.data_vencimento(self.HABITE_SE, 5), date(2029, 3, 15))

    def test_prazo_fracionario(self):
        self.assertEqual(g.data_vencimento(self.HABITE_SE, 0.5), date(2024, 9, 15))

    def test_sem_prazo(self):
        self.assertIsNone(g.data_vencimento(self.HABITE_SE, None))

    def test_dias_restantes(self):
        self.assertEqual(g.dias_restantes(date(2026, 9, 10), date(2026, 9, 8)), 2)
        self.assertEqual(g.dias_restantes(date(2026, 9, 1), date(2026, 9, 8)), -7)
        self.assertIsNone(g.dias_restantes(None, date(2026, 9, 8)))


class TestSituacao(unittest.TestCase):
    HOJE = date(2026, 9, 8)

    def situacao_em(self, vencimento):
        return g.situacao(vencimento, self.HOJE)

    def test_vencida(self):
        self.assertEqual(self.situacao_em(date(2026, 9, 7)), g.VENCIDA)

    def test_vence_hoje_ainda_nao_venceu(self):
        self.assertEqual(self.situacao_em(self.HOJE), g.VENCE_6)

    def test_limite_de_6_meses(self):
        self.assertEqual(self.situacao_em(date(2027, 3, 8)), g.VENCE_6)
        self.assertEqual(self.situacao_em(date(2027, 3, 9)), g.VENCE_12)

    def test_limite_de_12_meses(self):
        self.assertEqual(self.situacao_em(date(2027, 9, 8)), g.VENCE_12)
        self.assertEqual(self.situacao_em(date(2027, 9, 9)), g.VIGENTE)

    def test_sem_prazo_tipificado(self):
        self.assertEqual(self.situacao_em(None), g.SEM_PRAZO)


class TestAvaliar(unittest.TestCase):
    def test_quadro_completo_do_exemplo(self):
        q = g.avaliar(date(2024, 3, 15), 5, referencia=date(2026, 9, 8))
        self.assertEqual(q["data_vencimento"], date(2029, 3, 15))
        self.assertEqual(q["situacao"], g.VIGENTE)
        self.assertEqual(q["emoji"], "🟢")
        self.assertEqual(q["dias_restantes"], (date(2029, 3, 15) - date(2026, 9, 8)).days)
        self.assertIn("Manual da Edificacao", q["aviso"])

    def test_alerta_preventivo(self):
        # Habite-se + 3 anos -> 15/03/2027; a 6 meses e 7 dias da referencia
        perto = g.avaliar(date(2024, 3, 15), 3, referencia=date(2026, 9, 8))
        self.assertEqual(perto["situacao"], g.VENCE_12)
        self.assertTrue(g.em_alerta(perto))

        # duas semanas depois a mesma garantia entra na janela de 6 meses
        mais_perto = g.avaliar(date(2024, 3, 15), 3, referencia=date(2026, 9, 22))
        self.assertEqual(mais_perto["situacao"], g.VENCE_6)
        self.assertTrue(g.em_alerta(mais_perto))

        longe = g.avaliar(date(2024, 3, 15), 5, referencia=date(2026, 9, 8))
        self.assertFalse(g.em_alerta(longe))

    def test_sem_prazo_nao_dispara_alerta(self):
        self.assertFalse(g.em_alerta(g.avaliar(date(2024, 3, 15), None)))


if __name__ == "__main__":
    unittest.main()
