import unittest
from datetime import date

from tcc.services import gut


class TestGUT(unittest.TestCase):
    def test_produto(self):
        self.assertEqual(gut.calcular_gut(10, 10, 10), 1000)
        self.assertEqual(gut.calcular_gut(1, 1, 1), 1)
        self.assertEqual(gut.calcular_gut(8, 8, 8), 512)

    def test_valor_invalido(self):
        for ruim in (0, 2, 5, 7, 9, 11, -1):
            with self.assertRaises(ValueError):
                gut.calcular_gut(ruim, 10, 10)

    def test_faixas_de_prioridade(self):
        self.assertEqual(gut.prioridade(1000), 1)
        self.assertEqual(gut.prioridade(512), 1)     # limite inferior de P1
        self.assertEqual(gut.prioridade(511), 2)
        self.assertEqual(gut.prioridade(108), 2)     # limite inferior de P2
        self.assertEqual(gut.prioridade(107), 3)
        self.assertEqual(gut.prioridade(1), 3)

    def test_classificar_traz_rotulo(self):
        r = gut.classificar(10, 8, 8)                # 640
        self.assertEqual(r["gut"], 640)
        self.assertEqual(r["prioridade"], 1)
        self.assertEqual(r["emoji"], "🔴")


if __name__ == "__main__":
    unittest.main()
