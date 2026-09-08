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

    def test_semeadura_traz_o_catalogo_da_planilha(self):
        seed.semear_tudo(self.con)
        conta = lambda t: self.con.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"]
        self.assertEqual(conta("sistemas"), 9)
        self.assertEqual(conta("itens_catalogo"), 82)   # IT-001..IT-066 + T3-01..T3-16
        self.assertEqual(conta("regras_garantia"), 30)  # sintese de prazos da NBR 17170

    def test_distribuicao_de_prazos_do_catalogo(self):
        """Confere contra a planilha: 23 itens de 5 anos, 21 de 3, 18 de 1, 20 sem prazo."""
        seed.semear_tudo(self.con)
        contagem = {
            linha["prazo_anos"]: linha["n"]
            for linha in self.con.execute(
                "SELECT prazo_anos, COUNT(*) n FROM itens_catalogo GROUP BY prazo_anos"
            )
        }
        self.assertEqual(contagem[5.0], 23)
        self.assertEqual(contagem[3.0], 21)
        self.assertEqual(contagem[1.0], 18)
        self.assertEqual(contagem[None], 20)
        self.assertEqual(seed.itens_sem_prazo(self.con), 20)

    def test_itens_t3_nao_tem_prazo_em_anos(self):
        """A Tabela 3 nao estabelece prazo em anos -- identificacao na entrega."""
        seed.semear_tudo(self.con)
        com_prazo = self.con.execute(
            "SELECT COUNT(*) n FROM itens_catalogo "
            "WHERE id_item LIKE 'T3-%' AND prazo_anos IS NOT NULL"
        ).fetchone()["n"]
        self.assertEqual(com_prazo, 0)

    def test_todo_item_it_esta_ligado_a_um_sistema(self):
        seed.semear_tudo(self.con)
        orfaos = self.con.execute(
            "SELECT id_item FROM itens_catalogo "
            "WHERE id_item LIKE 'IT-%' AND sistema_id IS NULL"
        ).fetchall()
        self.assertEqual([l["id_item"] for l in orfaos], [])

    def test_semear_duas_vezes_nao_duplica(self):
        seed.semear_tudo(self.con)
        seed.semear_tudo(self.con)
        conta = lambda t: self.con.execute(f"SELECT COUNT(*) n FROM {t}").fetchone()["n"]
        self.assertEqual(conta("itens_catalogo"), 82)
        self.assertEqual(conta("regras_garantia"), 30)

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
