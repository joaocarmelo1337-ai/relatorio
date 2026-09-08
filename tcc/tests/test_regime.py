import unittest
from datetime import date, timedelta

from tcc.services import regime


class TestRegimeNormativo(unittest.TestCase):
    def test_limite_e_a_publicacao_mais_180_dias(self):
        self.assertEqual(
            regime.PUBLICACAO_NBR_17170 + timedelta(days=regime.DIAS_DE_VACANCIA),
            regime.LIMITE,
        )
        self.assertEqual(regime.LIMITE, date(2023, 6, 10))

    def test_protocolo_depois_do_limite(self):
        self.assertEqual(regime.regime_normativo(date(2023, 6, 11)), regime.NBR_17170)
        self.assertEqual(regime.regime_normativo(date(2024, 1, 1)), regime.NBR_17170)

    def test_no_proprio_limite_ainda_e_o_regime_anterior(self):
        # a regra da planilha e "POSTERIOR a 10/06/2023"
        self.assertEqual(regime.regime_normativo(date(2023, 6, 10)), regime.ANTERIOR)

    def test_protocolo_antes_do_limite(self):
        self.assertEqual(regime.regime_normativo(date(2022, 5, 1)), regime.ANTERIOR)

    def test_sem_data_de_protocolo(self):
        self.assertEqual(regime.regime_normativo(None), regime.INDEFINIDO)
        self.assertEqual(regime.regime_normativo(""), regime.INDEFINIDO)

    def test_aceita_data_em_texto(self):
        self.assertEqual(regime.regime_normativo("2024-03-15"), regime.NBR_17170)


class TestAlertaDeConsistencia(unittest.TestCase):
    def test_vistoria_antes_do_habite_se_dispara_alerta(self):
        aviso = regime.alerta_consistencia(date(2024, 3, 15), date(2024, 1, 10))
        self.assertIn("ATENÇÃO", aviso)

    def test_ordem_correta_das_datas(self):
        self.assertEqual(
            regime.alerta_consistencia(date(2024, 3, 15), date(2026, 9, 8)), "OK"
        )

    def test_datas_faltando(self):
        self.assertIsNone(regime.alerta_consistencia(None, date(2026, 9, 8)))


class TestIdadeDecimal(unittest.TestCase):
    def test_formula_da_planilha(self):
        from tcc.services import edificacao
        # (data da vistoria - data do habite-se) / 365,25
        idade = edificacao.idade_decimal(date(2024, 3, 15), date(2026, 9, 8))
        self.assertAlmostEqual(idade, (date(2026, 9, 8) - date(2024, 3, 15)).days / 365.25, places=6)
        self.assertAlmostEqual(idade, 2.48, places=2)

    def test_nunca_negativa(self):
        from tcc.services import edificacao
        self.assertEqual(edificacao.idade_decimal(date(2024, 3, 15), date(2023, 1, 1)), 0.0)


if __name__ == "__main__":
    unittest.main()
