import tempfile
import unittest
from datetime import date
from pathlib import Path

from tcc.database import db, seed
from tcc.services import ambientes, vistorias


class BaseVistoria(unittest.TestCase):
    HABITE_SE = "2024-03-15"
    DATA_VISTORIA = "2026-09-08"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.con = db.criar_banco(Path(self.tmp.name) / "teste.db")
        seed.semear_tudo(self.con)
        self.rid = self.con.execute(
            "INSERT INTO residencias (nome, data_habite_se, criado_em) VALUES (?,?,?)",
            ("Casa Silva", self.HABITE_SE, "2026-09-08"),
        ).lastrowid
        self.aid = ambientes.criar(self.con, self.rid, "Banheiro social")
        self.vid = vistorias.criar_vistoria(
            self.con, self.rid, self.DATA_VISTORIA, responsavel="João Carmelo"
        )
        self.con.commit()

    def tearDown(self):
        self.con.close()
        self.tmp.cleanup()

    def item_por_codigo(self, id_item):
        return self.con.execute(
            "SELECT id FROM itens_catalogo WHERE id_item = ?", (id_item,)
        ).fetchone()["id"]


class TestRegistro(BaseVistoria):
    def test_nao_conforme_vira_manifestacao_com_codigo(self):
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-037"),
            vistorias.NAO_CONFORME, ambiente_id=self.aid,
            descricao="Rejunte solto no box",
        )
        self.con.commit()
        linha = vistorias.ocorrencia(self.con, oid)
        self.assertEqual(linha["codigo"], "OCO-0001")
        self.assertEqual(linha["ambiente"], "Banheiro social")
        self.assertEqual(linha["sistema"], "Revestimento")

    def test_codigos_sao_sequenciais(self):
        item = self.item_por_codigo("IT-037")
        for _ in range(3):
            vistorias.registrar(self.con, self.vid, item, vistorias.NAO_CONFORME)
        self.con.commit()
        codigos = [l["codigo"] for l in vistorias.manifestacoes(self.con, self.rid)]
        self.assertEqual(sorted(codigos), ["OCO-0001", "OCO-0002", "OCO-0003"])

    def test_conforme_fica_registrado_mas_sem_codigo(self):
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-009"), vistorias.CONFORME
        )
        self.con.commit()
        self.assertIsNone(vistorias.ocorrencia(self.con, oid)["codigo"])
        self.assertEqual([], vistorias.manifestacoes(self.con, self.rid))

    def test_resultado_invalido_e_recusado(self):
        with self.assertRaises(ValueError):
            vistorias.registrar(
                self.con, self.vid, self.item_por_codigo("IT-009"), "Talvez"
            )

    def test_vistoria_inexistente_e_recusada(self):
        with self.assertRaises(ValueError):
            vistorias.registrar(
                self.con, 9999, self.item_por_codigo("IT-009"), vistorias.CONFORME
            )

    def test_origens_multiplas_voltam_como_lista(self):
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-021"),
            vistorias.NAO_CONFORME,
            origens=["Anomalia endógena", "Anomalia natural"],
        )
        self.con.commit()
        linha = vistorias.ocorrencia(self.con, oid)
        self.assertEqual(vistorias.origens_de(linha),
                         ["Anomalia endógena", "Anomalia natural"])

    def test_sem_origem_devolve_lista_vazia(self):
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-021"), vistorias.NAO_CONFORME
        )
        self.con.commit()
        self.assertEqual([], vistorias.origens_de(vistorias.ocorrencia(self.con, oid)))


class TestGarantiaNoRegistro(BaseVistoria):
    def test_item_de_5_anos_fica_vigente(self):
        # IT-009 estrutura, 5 anos: Habite-se 15/03/2024 -> vence 15/03/2029
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-009"), vistorias.NAO_CONFORME
        )
        self.con.commit()
        self.assertEqual(
            vistorias.ocorrencia(self.con, oid)["situacao_garantia"], "VIGENTE"
        )

    def test_item_de_1_ano_ja_venceu(self):
        # IT-037 rejuntamento, 1 ano: venceu em 15/03/2025
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-037"), vistorias.NAO_CONFORME
        )
        self.con.commit()
        self.assertEqual(
            vistorias.ocorrencia(self.con, oid)["situacao_garantia"], "VENCIDA"
        )

    def test_item_da_tabela_3_fica_sem_prazo(self):
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("T3-04"), vistorias.NAO_CONFORME
        )
        self.con.commit()
        self.assertEqual(
            vistorias.ocorrencia(self.con, oid)["situacao_garantia"],
            "SEM PRAZO TIPIFICADO",
        )

    def test_a_garantia_e_calculada_na_data_da_vistoria(self):
        """Uma vistoria antiga deve ver a garantia como ela estava naquele dia."""
        antiga = vistorias.criar_vistoria(self.con, self.rid, "2024-06-01")
        oid = vistorias.registrar(
            self.con, antiga, self.item_por_codigo("IT-037"), vistorias.NAO_CONFORME
        )
        self.con.commit()
        # rejuntamento vencia em 15/03/2025: em 01/06/2024 ainda estava correndo
        self.assertEqual(
            vistorias.ocorrencia(self.con, oid)["situacao_garantia"],
            "VENCE EM ATE 12 MESES",
        )


class TestClassificacaoGUT(BaseVistoria):
    def registrar_uma(self):
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-009"), vistorias.NAO_CONFORME
        )
        self.con.commit()
        return oid

    def test_classificar_calcula_gut_e_prioridade(self):
        oid = self.registrar_uma()
        resultado = vistorias.classificar(self.con, oid, 10, 8, 8,
                                          confirmada_por="João Carmelo")
        self.con.commit()
        self.assertEqual(resultado["gut"], 640)
        linha = vistorias.ocorrencia(self.con, oid)
        self.assertEqual(linha["gut"], 640)
        self.assertEqual(linha["prioridade"], 1)
        self.assertEqual(linha["confirmada_por"], "João Carmelo")

    def test_reclassificar_atualiza_em_vez_de_duplicar(self):
        oid = self.registrar_uma()
        vistorias.classificar(self.con, oid, 10, 10, 10)
        vistorias.classificar(self.con, oid, 3, 3, 3, justificativa="Reavaliado")
        self.con.commit()
        linhas = self.con.execute(
            "SELECT * FROM classificacoes_gut WHERE ocorrencia_id = ?", (oid,)
        ).fetchall()
        self.assertEqual(len(linhas), 1)
        self.assertEqual(linhas[0]["gut"], 27)
        self.assertEqual(linhas[0]["prioridade"], 3)
        self.assertEqual(linhas[0]["justificativa"], "Reavaliado")

    def test_valor_fora_da_escala_e_recusado(self):
        oid = self.registrar_uma()
        with self.assertRaises(ValueError):
            vistorias.classificar(self.con, oid, 7, 8, 8)

    def test_manifestacoes_saem_ordenadas_pelo_gut(self):
        baixa = self.registrar_uma()
        alta = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-021"), vistorias.NAO_CONFORME
        )
        vistorias.classificar(self.con, baixa, 1, 1, 1)
        vistorias.classificar(self.con, alta, 10, 10, 10)
        self.con.commit()
        lista = vistorias.manifestacoes(self.con, self.rid)
        self.assertEqual([l["gut"] for l in lista], [1000, 1])


class TestAlertaDeGarantia(BaseVistoria):
    def test_alerta_quando_a_garantia_esta_acabando(self):
        # IT-006 muro, 3 anos: vence 15/03/2027, a ~6 meses da vistoria
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-006"),
            vistorias.NAO_CONFORME, descricao="Fissura no muro de divisa",
        )
        vistorias.classificar(self.con, oid, 6, 6, 6)
        self.con.commit()

        alerta = vistorias.alerta_de_garantia(self.con, oid)
        self.assertIsNotNone(alerta)
        self.assertEqual(alerta["codigo"], "OCO-0001")
        self.assertEqual(alerta["situacao"], "VENCE EM ATE 12 MESES")
        self.assertEqual(alerta["prioridade"], 2)
        self.assertIn("Manual da Edificacao", alerta["aviso"])

    def test_sem_alerta_quando_a_garantia_esta_longe(self):
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-009"), vistorias.NAO_CONFORME
        )
        self.con.commit()
        self.assertIsNone(vistorias.alerta_de_garantia(self.con, oid))

    def test_sem_alerta_para_item_sem_prazo(self):
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("T3-04"), vistorias.NAO_CONFORME
        )
        self.con.commit()
        self.assertIsNone(vistorias.alerta_de_garantia(self.con, oid))

    def test_conforme_nao_gera_alerta(self):
        oid = vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-006"), vistorias.CONFORME
        )
        self.con.commit()
        self.assertIsNone(vistorias.alerta_de_garantia(self.con, oid))

    def test_lista_de_alertas_da_residencia(self):
        for id_item in ("IT-006", "IT-037", "IT-009"):
            vistorias.registrar(
                self.con, self.vid, self.item_por_codigo(id_item),
                vistorias.NAO_CONFORME,
            )
        self.con.commit()
        alertas = vistorias.manifestacoes_em_alerta(self.con, self.rid)
        # IT-006 vence em breve, IT-037 ja venceu, IT-009 esta longe
        self.assertEqual(len(alertas), 2)


class TestHistorico(BaseVistoria):
    def test_vistoria_e_ocorrencia_entram_na_linha_do_tempo(self):
        vistorias.registrar(
            self.con, self.vid, self.item_por_codigo("IT-037"),
            vistorias.NAO_CONFORME, descricao="Rejunte solto",
        )
        self.con.commit()
        linha_do_tempo = vistorias.historico(self.con, self.rid)
        tipos = [l["tipo"] for l in linha_do_tempo]
        self.assertIn("vistoria", tipos)
        self.assertIn("ocorrencia", tipos)

    def test_historico_sai_em_ordem_cronologica(self):
        vistorias.criar_vistoria(self.con, self.rid, "2027-03-10", tipo="Reinspeção")
        self.con.commit()
        datas = [l["data_evento"] for l in vistorias.historico(self.con, self.rid)]
        self.assertEqual(datas, sorted(datas))


if __name__ == "__main__":
    unittest.main()
