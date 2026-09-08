import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from tcc.services import pacote_campo as pc


def manifesto_valido():
    return {
        "versao": 1,
        "aplicativo": "app-campo",
        "residencia": {"nome": "Casa Silva", "data_habite_se": "2024-03-15"},
        "vistoria": {"data_vistoria": "2026-09-08", "responsavel": "Joao Carmelo"},
        "ambientes": [{"nome": "Banheiro social"}],
        "ocorrencias": [
            {
                "uuid": "oco-1",
                "ambiente": "Banheiro social",
                "sistema": "impermeabilizacao",
                "tipo_manifestacao": "Infiltracao",
                "descricao": "Mancha de umidade no encontro parede/piso",
                "resultado": "Nao Conforme",
            }
        ],
        "fotos": [
            {
                "uuid": "foto-1",
                "arquivo": "foto-1.jpg",
                "ocorrencia_uuid": "oco-1",
                "legenda": "Encontro parede/piso",
                "momento": "antes",
            }
        ],
    }


def montar_zip(caminho, manifesto, fotos=(("foto-1.jpg", b"conteudo-jpeg"),)):
    with zipfile.ZipFile(caminho, "w") as z:
        z.writestr("manifesto.json", json.dumps(manifesto, ensure_ascii=False))
        for nome, dados in fotos:
            z.writestr(f"fotos/{nome}", dados)
    return caminho


class TestPacote(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.zip = self.dir / "vistoria.zip"

    def tearDown(self):
        self.tmp.cleanup()

    def test_le_pacote_valido(self):
        montar_zip(self.zip, manifesto_valido())
        m = pc.ler_manifesto(self.zip)
        self.assertEqual(pc.resumo(m), {
            "residencia": "Casa Silva",
            "data_vistoria": "2026-09-08",
            "ambientes": 1,
            "ocorrencias": 1,
            "fotos": 1,
        })

    def test_recusa_arquivo_que_nao_e_zip(self):
        solto = self.dir / "qualquer.zip"
        solto.write_bytes(b"isto nao e um zip")
        with self.assertRaises(pc.PacoteInvalido):
            pc.ler_manifesto(solto)

    def test_recusa_zip_sem_manifesto(self):
        with zipfile.ZipFile(self.zip, "w") as z:
            z.writestr("fotos/foto-1.jpg", b"x")
        with self.assertRaises(pc.PacoteInvalido):
            pc.ler_manifesto(self.zip)

    def test_recusa_versao_desconhecida(self):
        m = manifesto_valido()
        m["versao"] = 99
        montar_zip(self.zip, m)
        with self.assertRaises(pc.PacoteInvalido):
            pc.ler_manifesto(self.zip)

    def test_recusa_uuid_repetido(self):
        m = manifesto_valido()
        m["fotos"].append(dict(m["fotos"][0]))
        montar_zip(self.zip, m)
        with self.assertRaises(pc.PacoteInvalido):
            pc.ler_manifesto(self.zip)

    def test_recusa_foto_apontando_para_ocorrencia_inexistente(self):
        m = manifesto_valido()
        m["fotos"][0]["ocorrencia_uuid"] = "nao-existe"
        montar_zip(self.zip, m)
        with self.assertRaises(pc.PacoteInvalido):
            pc.ler_manifesto(self.zip)

    def test_confere_fotos_faltando_e_sobrando(self):
        m = manifesto_valido()
        m["fotos"].append({"uuid": "foto-2", "arquivo": "foto-2.jpg"})
        montar_zip(self.zip, m, fotos=(("foto-1.jpg", b"a"), ("extra.jpg", b"b")))
        faltando, sobrando = pc.conferir_fotos(self.zip)
        self.assertEqual(faltando, ["foto-2.jpg"])
        self.assertEqual(sobrando, ["extra.jpg"])

    def test_extrai_com_nome_pelo_uuid(self):
        montar_zip(self.zip, manifesto_valido())
        destino = self.dir / "uploads" / "casa-silva"
        mapa = pc.extrair_fotos(self.zip, destino)
        self.assertEqual(set(mapa), {"foto-1"})
        self.assertEqual(mapa["foto-1"].name, "foto-1.jpg")
        self.assertTrue(mapa["foto-1"].exists())

    def test_extrair_duas_vezes_nao_duplica(self):
        montar_zip(self.zip, manifesto_valido())
        destino = self.dir / "uploads"
        pc.extrair_fotos(self.zip, destino)
        pc.extrair_fotos(self.zip, destino)
        self.assertEqual(len(list(destino.iterdir())), 1)

    def test_nome_malicioso_no_zip_nao_escapa_da_pasta(self):
        m = manifesto_valido()
        m["fotos"][0]["arquivo"] = "../../../etc/foto-1.jpg"
        montar_zip(self.zip, m, fotos=(("foto-1.jpg", b"x"),))
        destino = self.dir / "uploads"
        mapa = pc.extrair_fotos(self.zip, destino)
        self.assertEqual(mapa["foto-1"].parent.resolve(), destino.resolve())

    def test_recusa_extensao_estranha(self):
        m = manifesto_valido()
        m["fotos"][0]["arquivo"] = "foto-1.exe"
        montar_zip(self.zip, m, fotos=(("foto-1.exe", b"x"),))
        with self.assertRaises(pc.PacoteInvalido):
            pc.extrair_fotos(self.zip, self.dir / "uploads")


if __name__ == "__main__":
    unittest.main()
