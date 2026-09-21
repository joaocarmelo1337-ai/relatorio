"""Teste de fumaça: exercita as rotas principais em um banco temporário.

    python teste_smoke.py
"""
import base64
import io
import json
import os
import re
import sqlite3
import struct
import sys
import tempfile
import zlib

BANCO = os.path.join(tempfile.mkdtemp(prefix="epi-teste-"), "teste.sqlite3")
os.environ["EPI_DATABASE"] = BANCO
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app as appmod   # noqa: E402


def png(largura=240, altura=80):
    """PNG mínimo com um traço horizontal, no lugar de uma assinatura de verdade."""
    linhas = b""
    for y in range(altura):
        fila = bytearray([0])
        for x in range(largura):
            escuro = abs(y - altura // 2) < 3 and 10 < x < largura - 10
            fila += bytes([0, 0, 0] if escuro else [255, 255, 255])
        linhas += bytes(fila)

    def bloco(tipo, dados):
        return struct.pack(">I", len(dados)) + tipo + dados + struct.pack(">I", zlib.crc32(tipo + dados))

    return (b"\x89PNG\r\n\x1a\n"
            + bloco(b"IHDR", struct.pack(">IIBBBBB", largura, altura, 8, 2, 0, 0, 0))
            + bloco(b"IDAT", zlib.compress(linhas))
            + bloco(b"IEND", b""))


def principal():
    aplicativo = appmod.create_app()
    c = aplicativo.test_client()
    assinatura = "data:image/png;base64," + base64.b64encode(png()).decode()

    def ok(resposta, esperado, rotulo):
        assert resposta.status_code in esperado, (rotulo, resposta.status_code, resposta.data[:400])
        return resposta

    for rota in ["/", "/funcionarios", "/epis", "/configuracoes"]:
        ok(c.get(rota, follow_redirects=True), (200,), rota)
    print("· páginas principais respondem")

    ok(c.post("/configuracoes", data={
        "nome": "CONSTRUTORA EXEMPLO LTDA", "cnpj": "12.345.678/0001-90",
        "logo": (io.BytesIO(png(200, 60)), "logo.png")},
        content_type="multipart/form-data"), (302,), "configuracoes")
    assert c.get("/empresa/logo").status_code == 200
    assert "CONSTRUTORA EXEMPLO LTDA" in c.get("/funcionarios").get_data(as_text=True)
    print("· nome e logo da empresa gravados e usados no cabeçalho")

    r = ok(c.post("/funcionarios/novo", data={
        "nome": "MARIA DA SILVA", "registro": "1234", "cargo": "AUXILIAR", "setor": "OBRA",
        "ciente_data": "2026-03-02", "assinatura": assinatura}), (302,), "novo funcionário")
    fid = int(r.headers["Location"].rstrip("/").split("/")[-1])

    pagina = c.get(f"/funcionarios/{fid}/entregas/nova").get_data(as_text=True)
    epis = json.loads(re.search(r'id="dados-epis">\s*(\[.*?\])\s*</script>', pagina, re.S).group(1))
    camisa = next(e for e in epis if e["nome"] == "CAMISA")
    calcado = next(e for e in epis if e["nome"].startswith("CALÇADO"))
    assert calcado["ca"] == "28513", "CA padrão do calçado não foi pré-carregado"

    # a ficha em papel só tem tamanho em camisa, camisa polo, calça e jaleco;
    # calçado vai por numeração e o resto não tem tamanho nenhum
    por_nome = {e["nome"]: e["tem_tamanho"] for e in epis}
    for nome in ("CAMISA", "CAMISA POLO", "CALÇA", "JALECO"):
        assert por_nome[nome] == 1, f"{nome} deveria ter tamanho P/M/G/GG/EXG"
    assert por_nome["CALÇADO DE SEGURANÇA"] == 2, "calçado deveria ir por numeração"
    for nome in ("LUVA VAQUETA", "LUVA PU", "COLETE REFLETIVO", "ÓCULOS DE SEGURANÇA",
                 "PROTETOR AURICULAR PLUG", "CAPACETE COM JUGULAR", "AVENTAL DE RASPA"):
        assert por_nome[nome] == 0, f"{nome} não deveria pedir tamanho"
    print("· tamanhos da lista mestre conferem com a planilha")

    # cada material vai com a SUA assinatura; o último fica sem, de propósito
    ok(c.post(f"/funcionarios/{fid}/entregas/nova", data={
        "data_inicio": "2026-03-01", "data_entrega": "2026-03-02",
        "item_epi_id[]": [str(camisa["id"]), str(calcado["id"]), ""],
        "item_nome[]": ["CAMISA", "CALÇADO DE SEGURANÇA", "luva nitrílica"],
        "item_ca[]": ["", "28513", "41234"],
        "item_qtde[]": ["2", "1", "3"],
        "item_tamanho[]": ["GG", "41", ""],
        "item_salvar[]": ["0", "0", "1"],
        "item_assinatura[]": [assinatura, assinatura, ""],
        "item_assinatura_id[]": ["", "", ""],
        "item_assinatura_apagar[]": ["0", "0", "0"],
        "item_data_devolucao[]": ["", "", ""],
        "item_assinatura_devolucao_id[]": ["", "", ""],
        "observacoes": "Entrega de admissão"}), (302,), "nova entrega")

    ficha = c.get(f"/funcionarios/{fid}").get_data(as_text=True)
    assert "LUVA NITRÍLICA" in ficha and "CALÇADO DE SEGURANÇA" in ficha and "GG" in ficha
    assert "LUVA NITRÍLICA" in c.get("/epis").get_data(as_text=True), "item novo não foi salvo na lista mestre"
    print("· entrega registrada e item novo salvo na lista mestre")

    con = sqlite3.connect(BANCO)
    con.row_factory = sqlite3.Row
    eid = con.execute("SELECT id FROM entregas ORDER BY id").fetchone()["id"]
    itens = con.execute(
        "SELECT id, nome, assinatura_id FROM entrega_itens WHERE entrega_id = ? ORDER BY ordem", (eid,)
    ).fetchall()
    assert itens[0]["assinatura_id"] and itens[1]["assinatura_id"], "assinatura por material não gravou"
    assert itens[0]["assinatura_id"] != itens[1]["assinatura_id"], "os materiais dividiram a mesma assinatura"
    assert itens[2]["assinatura_id"] is None, "item sem assinatura deveria ficar sem"
    print("· cada material guardou a sua própria assinatura")

    # devolve só o primeiro material, com assinatura própria
    ok(c.post(f"/entregas/{eid}/devolucao", data={
        "data_devolucao": "2026-08-01",
        "devolver[]": [str(itens[0]["id"])],
        f"assinatura_{itens[0]['id']}": assinatura}), (302,), "devolução")
    depois = con.execute(
        "SELECT id, data_devolucao, assinatura_devolucao_id FROM entrega_itens WHERE entrega_id = ? ORDER BY ordem",
        (eid,)).fetchall()
    assert depois[0]["data_devolucao"] == "2026-08-01" and depois[0]["assinatura_devolucao_id"]
    assert depois[1]["data_devolucao"] is None, "material não marcado não deveria constar como devolvido"
    print("· devolução registrada material a material")

    r = c.get(f"/funcionarios/{fid}/pdf")
    assert r.status_code == 200 and r.data[:4] == b"%PDF", (r.status_code, r.data[:200])
    print(f"· PDF gerado ({len(r.data)} bytes)")

    r = c.post("/funcionarios/novo", data={"nome": "FUNCIONÁRIO SEM ENTREGA"})
    fid2 = int(r.headers["Location"].rstrip("/").split("/")[-1])
    assert c.get(f"/funcionarios/{fid2}/pdf").data[:4] == b"%PDF"
    ok(c.post(f"/funcionarios/{fid2}/excluir"), (302,), "excluir funcionário")
    print("· ficha sem entregas e exclusão de funcionário")

    print("\nTudo certo. Banco de teste em", BANCO)


if __name__ == "__main__":
    principal()
