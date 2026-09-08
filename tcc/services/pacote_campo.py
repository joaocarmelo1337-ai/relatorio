"""Pacote de vistoria: o formato de troca entre o app de campo e a plataforma.

O celular (app offline) exporta UM arquivo .zip por vistoria:

    vistoria_casa-silva_2026-09-08.zip
    |- manifesto.json          dados da vistoria, ambientes, ocorrencias e fotos
    |- fotos/
       |- 8f3a...c1.jpg        nome do arquivo = uuid da foto
       |- 2b90...7e.jpg

A plataforma importa esse zip. A importacao e IDEMPOTENTE: cada ocorrencia
e cada foto carregam um uuid gerado no celular, entao reimportar o mesmo
pacote (ou um pacote que repete fotos de uma exportacao anterior) nao
duplica nada. Por isso o celular nunca precisa apagar nada para exportar.

Tudo aqui e biblioteca padrao -- roda sem pandas e sem Streamlit.
"""

import hashlib
import json
import shutil
import zipfile
from pathlib import Path

VERSAO_FORMATO = 1
MANIFESTO = "manifesto.json"
PASTA_FOTOS = "fotos"

EXTENSOES_ACEITAS = {".jpg", ".jpeg", ".png", ".webp"}


class PacoteInvalido(Exception):
    """O zip nao tem a cara de um pacote de vistoria."""


def _exigir(condicao, mensagem):
    if not condicao:
        raise PacoteInvalido(mensagem)


def sha256_de(caminho):
    digest = hashlib.sha256()
    with open(caminho, "rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            digest.update(bloco)
    return digest.hexdigest()


def ler_manifesto(caminho_zip):
    """Le e valida o manifesto sem extrair nada. Levanta PacoteInvalido."""
    try:
        with zipfile.ZipFile(caminho_zip) as z:
            nomes = set(z.namelist())
            _exigir(MANIFESTO in nomes, f"o pacote nao contem {MANIFESTO}")
            try:
                manifesto = json.loads(z.read(MANIFESTO).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as erro:
                raise PacoteInvalido(f"{MANIFESTO} ilegivel: {erro}") from erro
    except zipfile.BadZipFile as erro:
        raise PacoteInvalido(f"arquivo nao e um zip valido: {erro}") from erro

    validar_manifesto(manifesto)
    return manifesto


def validar_manifesto(manifesto):
    _exigir(isinstance(manifesto, dict), "manifesto deve ser um objeto JSON")
    versao = manifesto.get("versao")
    _exigir(versao == VERSAO_FORMATO,
            f"versao de formato {versao!r} nao suportada (esperado {VERSAO_FORMATO})")

    residencia = manifesto.get("residencia")
    _exigir(isinstance(residencia, dict), "manifesto sem o bloco 'residencia'")
    _exigir(residencia.get("nome"), "a residencia precisa de um nome")

    vistoria = manifesto.get("vistoria")
    _exigir(isinstance(vistoria, dict), "manifesto sem o bloco 'vistoria'")
    _exigir(vistoria.get("data_vistoria"), "a vistoria precisa de data_vistoria")

    uuids_ocorrencia = set()
    for ocorrencia in manifesto.get("ocorrencias", []):
        uuid = ocorrencia.get("uuid")
        _exigir(uuid, "ocorrencia sem uuid")
        _exigir(uuid not in uuids_ocorrencia, f"uuid de ocorrencia repetido: {uuid}")
        uuids_ocorrencia.add(uuid)

    uuids_foto = set()
    for foto in manifesto.get("fotos", []):
        uuid = foto.get("uuid")
        _exigir(uuid, "foto sem uuid")
        _exigir(uuid not in uuids_foto, f"uuid de foto repetido: {uuid}")
        uuids_foto.add(uuid)
        _exigir(foto.get("arquivo"), f"foto {uuid} sem nome de arquivo")
        vinculo = foto.get("ocorrencia_uuid")
        _exigir(
            vinculo is None or vinculo in uuids_ocorrencia,
            f"foto {uuid} aponta para ocorrencia inexistente: {vinculo}",
        )
    return manifesto


def conferir_fotos(caminho_zip, manifesto=None):
    """Confere se toda foto do manifesto existe no zip, e vice-versa.

    Devolve (faltando_no_zip, sobrando_no_zip).
    """
    manifesto = manifesto or ler_manifesto(caminho_zip)
    declaradas = {f["arquivo"] for f in manifesto.get("fotos", [])}
    with zipfile.ZipFile(caminho_zip) as z:
        presentes = {
            Path(nome).name
            for nome in z.namelist()
            if nome.startswith(PASTA_FOTOS + "/") and not nome.endswith("/")
        }
    return sorted(declaradas - presentes), sorted(presentes - declaradas)


def extrair_fotos(caminho_zip, destino, manifesto=None):
    """Extrai as fotos para `destino`, devolvendo {uuid: caminho_final}.

    Nao confia nos nomes de dentro do zip (path traversal): grava sempre
    como <uuid><extensao>. Se o arquivo ja existe com o mesmo conteudo,
    reaproveita em vez de regravar.
    """
    manifesto = manifesto or ler_manifesto(caminho_zip)
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)

    resultado = {}
    with zipfile.ZipFile(caminho_zip) as z:
        for foto in manifesto.get("fotos", []):
            nome_interno = f"{PASTA_FOTOS}/{Path(foto['arquivo']).name}"
            if nome_interno not in z.namelist():
                raise PacoteInvalido(f"foto declarada mas ausente no zip: {nome_interno}")

            extensao = Path(foto["arquivo"]).suffix.lower()
            if extensao not in EXTENSOES_ACEITAS:
                raise PacoteInvalido(
                    f"extensao nao aceita em {foto['arquivo']}: {extensao}"
                )

            final = destino / f"{foto['uuid']}{extensao}"
            if not final.exists():
                with z.open(nome_interno) as origem, open(final, "wb") as saida:
                    shutil.copyfileobj(origem, saida)
            resultado[foto["uuid"]] = final
    return resultado


def resumo(manifesto):
    """Uma linha para a tela de importacao, antes de confirmar."""
    return {
        "residencia": manifesto["residencia"]["nome"],
        "data_vistoria": manifesto["vistoria"]["data_vistoria"],
        "ambientes": len(manifesto.get("ambientes", [])),
        "ocorrencias": len(manifesto.get("ocorrencias", [])),
        "fotos": len(manifesto.get("fotos", [])),
    }
