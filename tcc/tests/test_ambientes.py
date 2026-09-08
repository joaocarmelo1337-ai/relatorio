import tempfile
import unittest
from pathlib import Path

from tcc.database import db, seed
from tcc.services import ambientes


class TestAmbientes(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.con = db.criar_banco(Path(self.tmp.name) / "teste.db")
        seed.semear_tudo(self.con)
        self.rid = self.con.execute(
            "INSERT INTO residencias (nome, criado_em) VALUES ('Casa Silva', '2026-09-08')"
        ).lastrowid
        self.con.commit()

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def test_criar_e_listar(self):
        ambientes.criar(self.con, self.rid, "Banheiro social")
        ambientes.criar(self.con, self.rid, "Cozinha")
        self.assertEqual(["Banheiro social", "Cozinha"],
                         sorted(ambientes.nomes(self.con, self.rid)))

    def test_nome_vazio_e_recusado(self):
        for ruim in ("", "   ", None):
            with self.assertRaises(ValueError):
                ambientes.criar(self.con, self.rid, ruim)

    def test_nome_repetido_e_recusado_ignorando_caixa(self):
        ambientes.criar(self.con, self.rid, "Cozinha")
        with self.assertRaises(ValueError):
            ambientes.criar(self.con, self.rid, "cozinha")
        with self.assertRaises(ValueError):
            ambientes.criar(self.con, self.rid, "  COZINHA  ")

    def test_mesmo_nome_em_outra_residencia_e_permitido(self):
        outra = self.con.execute(
            "INSERT INTO residencias (nome, criado_em) VALUES ('Casa Souza', '2026-09-08')"
        ).lastrowid
        ambientes.criar(self.con, self.rid, "Cozinha")
        ambientes.criar(self.con, outra, "Cozinha")
        self.assertEqual(["Cozinha"], ambientes.nomes(self.con, outra))

    def test_sugestoes_escondem_o_que_ja_existe(self):
        antes = ambientes.sugestoes(self.con, self.rid)
        self.assertIn("Cozinha", antes)
        ambientes.criar(self.con, self.rid, "Cozinha")
        depois = ambientes.sugestoes(self.con, self.rid)
        self.assertNotIn("Cozinha", depois)
        self.assertEqual(len(antes) - 1, len(depois))

    def test_criar_varios_pula_os_repetidos(self):
        ambientes.criar(self.con, self.rid, "Sala")
        criados = ambientes.criar_varios(self.con, self.rid, ["Sala", "Quarto 01", "Suíte"])
        self.assertEqual(criados, 2)
        self.assertEqual(3, len(ambientes.nomes(self.con, self.rid)))

    def test_ordem_segue_a_criacao(self):
        ambientes.criar_varios(self.con, self.rid, ["Fachada", "Sala", "Cozinha"])
        self.assertEqual(["Fachada", "Sala", "Cozinha"],
                         [l["nome"] for l in ambientes.listar(self.con, self.rid)])

    def test_contagem_de_manifestacoes(self):
        aid = ambientes.criar(self.con, self.rid, "Banheiro social")
        for resultado in ("Nao Conforme", "Nao Conforme", "Conforme"):
            self.con.execute(
                "INSERT INTO ocorrencias (residencia_id, ambiente_id, resultado, criado_em) "
                "VALUES (?,?,?,?)", (self.rid, aid, resultado, "2026-09-08"))
        self.con.commit()
        linha = ambientes.listar(self.con, self.rid)[0]
        self.assertEqual(linha["manifestacoes"], 2)  # o 'Conforme' nao conta

    def test_renomear(self):
        aid = ambientes.criar(self.con, self.rid, "Quarto")
        ambientes.renomear(self.con, self.rid, aid, "Quarto 01")
        self.assertEqual(["Quarto 01"], ambientes.nomes(self.con, self.rid))

    def test_renomear_para_nome_existente_e_recusado(self):
        ambientes.criar(self.con, self.rid, "Sala")
        aid = ambientes.criar(self.con, self.rid, "Cozinha")
        with self.assertRaises(ValueError):
            ambientes.renomear(self.con, self.rid, aid, "Sala")

    def test_excluir_ambiente_preserva_as_manifestacoes(self):
        aid = ambientes.criar(self.con, self.rid, "Banheiro social")
        self.con.execute(
            "INSERT INTO ocorrencias (residencia_id, ambiente_id, resultado, descricao, criado_em) "
            "VALUES (?,?,?,?,?)",
            (self.rid, aid, "Nao Conforme", "Infiltração no rodapé", "2026-09-08"))
        self.con.commit()

        soltas = ambientes.excluir(self.con, aid)
        self.con.commit()

        self.assertEqual(soltas, 1)
        self.assertEqual([], ambientes.nomes(self.con, self.rid))
        linha = self.con.execute("SELECT * FROM ocorrencias").fetchone()
        self.assertEqual(linha["descricao"], "Infiltração no rodapé")
        self.assertIsNone(linha["ambiente_id"])


if __name__ == "__main__":
    unittest.main()
