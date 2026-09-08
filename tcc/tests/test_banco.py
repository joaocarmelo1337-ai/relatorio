import tempfile
import unittest
from datetime import date
from pathlib import Path

from tcc.database import db, seed


class TestBanco(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.caminho = Path(self.tmp.name) / "teste.db"
        self.con = db.criar_banco(self.caminho)

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def test_cria_as_tabelas_previstas(self):
        esperadas = {
            "usuarios", "residencias", "ambientes", "vistorias", "itens_catalogo",
            "ocorrencias", "classificacoes_gut", "fotos", "garantias",
            "manutencoes", "protocolos", "documentos", "historico",
            "sistemas", "regras_garantia",
        }
        self.assertEqual(esperadas, set(db.tabelas(self.con)))

    def test_criar_banco_e_idempotente(self):
        db.criar_banco(self.caminho).close()
        self.assertIn("residencias", db.tabelas(self.con))

    def test_semeadura(self):
        seed.semear_tudo(self.con)
        n_sistemas = self.con.execute("SELECT COUNT(*) n FROM sistemas").fetchone()["n"]
        n_regras = self.con.execute("SELECT COUNT(*) n FROM regras_garantia").fetchone()["n"]
        self.assertEqual(n_sistemas, 10)
        self.assertEqual(n_regras, 14)
        # nenhuma regra entra conferida: os prazos ainda vem da norma
        self.assertEqual(seed.regras_pendentes_de_conferencia(self.con), 14)

    def test_semear_duas_vezes_nao_duplica(self):
        seed.semear_tudo(self.con)
        seed.semear_tudo(self.con)
        n = self.con.execute("SELECT COUNT(*) n FROM regras_garantia").fetchone()["n"]
        self.assertEqual(n, 14)

    def test_senha_nunca_em_texto_puro(self):
        seed.semear_tudo(self.con, senha_admin="segredo")
        linha = self.con.execute("SELECT * FROM usuarios WHERE usuario='admin'").fetchone()
        self.assertNotEqual(linha["senha_hash"], "segredo")
        self.assertTrue(seed.conferir_senha("segredo", linha["senha_hash"], linha["salt"]))
        self.assertFalse(seed.conferir_senha("errada", linha["senha_hash"], linha["salt"]))

    def test_apagar_residencia_leva_junto_os_filhos(self):
        agora = "2026-09-08T00:00:00"
        cur = self.con.execute(
            "INSERT INTO residencias (nome, data_habite_se, criado_em) VALUES (?,?,?)",
            ("Casa Silva", "2024-03-15", agora),
        )
        rid = cur.lastrowid
        self.con.execute(
            "INSERT INTO ambientes (residencia_id, nome, criado_em) VALUES (?,?,?)",
            (rid, "Banheiro social", agora),
        )
        self.con.execute(
            "INSERT INTO ocorrencias (residencia_id, criado_em) VALUES (?,?)",
            (rid, agora),
        )
        self.con.commit()
        self.con.execute("DELETE FROM residencias WHERE id = ?", (rid,))
        self.con.commit()
        for tabela in ("ambientes", "ocorrencias"):
            n = self.con.execute(f"SELECT COUNT(*) n FROM {tabela}").fetchone()["n"]
            self.assertEqual(n, 0, f"sobrou registro orfao em {tabela}")

    def test_uuid_de_campo_impede_importacao_duplicada(self):
        agora = "2026-09-08T00:00:00"
        cur = self.con.execute(
            "INSERT INTO residencias (nome, criado_em) VALUES (?,?)", ("Casa A", agora)
        )
        rid = cur.lastrowid
        self.con.execute(
            "INSERT INTO ocorrencias (residencia_id, uuid_campo, criado_em) VALUES (?,?,?)",
            (rid, "abc-123", agora),
        )
        self.con.commit()
        with self.assertRaises(Exception):
            self.con.execute(
                "INSERT INTO ocorrencias (residencia_id, uuid_campo, criado_em) VALUES (?,?,?)",
                (rid, "abc-123", agora),
            )
            self.con.commit()


if __name__ == "__main__":
    unittest.main()
