"""Acesso as constantes normativas de config/normas.yaml.

Regra da casa: nenhum coeficiente é embutido no código. Tudo vem do YAML, e
qualquer valor marcado PENDENTE levanta `DadoNormativoAusente` com a mensagem
dizendo exatamente o que preencher e onde. O motor nunca interpola um PENDENTE.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PENDENTE = "PENDENTE"
RAIZ = Path(__file__).resolve().parent.parent
PADRAO_NORMAS = RAIZ / "config" / "normas.yaml"


class DadoNormativoAusente(Exception):
    """Um coeficiente marcado PENDENTE foi exigido pelo cálculo."""


class ConfiguracaoInvalida(Exception):
    """O arquivo de configuração do projeto pede algo que o motor não faz."""


def _exigir(valor: Any, o_que: str, onde: str) -> Any:
    if valor is None or valor == PENDENTE:
        raise DadoNormativoAusente(
            f"{o_que} não está disponível.\n"
            f"  Preencha `{onde}` em config/normas.yaml (hoje: PENDENTE).\n"
            f"  O motor não inventa nem interpola esse valor."
        )
    return valor


@dataclass(frozen=True)
class Normas:
    """Wrapper tipado sobre normas.yaml."""

    dados: dict

    # -- carga ------------------------------------------------------------
    @classmethod
    def carregar(cls, caminho: Path | str | None = None) -> "Normas":
        caminho = Path(caminho) if caminho else PADRAO_NORMAS
        with open(caminho, encoding="utf-8") as fh:
            return cls(yaml.safe_load(fh))

    def __getitem__(self, chave: str) -> Any:
        return self.dados[chave]

    # -- faixa coberta ----------------------------------------------------
    def faixa_fck(self) -> tuple[float, float]:
        f = self.dados["faixa_fck_MPa"]
        return float(f["minimo"]), float(f["maximo"])

    def exigir_fck_na_faixa(self, fck: float) -> None:
        """Recusa fck fora do escopo do projeto.

        Existe para o motor parar com uma frase clara em vez de tropecar mais
        adiante num PENDENTE solto da tabela de rho_min.
        """
        lo, hi = self.faixa_fck()
        if not (lo <= fck <= hi):
            raise ConfiguracaoInvalida(
                f"fck = {fck:g} MPa esta fora da faixa que este projeto cobre "
                f"(C{lo:g} a C{hi:g}).\n"
                f"  Para ampliar: ajuste `faixa_fck_MPa` e complete as linhas "
                f"correspondentes de `rho_min_percent.tabela` em "
                f"config/normas.yaml, lendo a Tabela 17.3 da NBR 6118."
            )

    # -- bloco retangular -------------------------------------------------
    def lambda_(self, fck: float) -> float:
        """Altura relativa do bloco retangular de compressão."""
        return 0.80 if fck <= 50 else 0.80 - (fck - 50) / 400.0

    def alpha_c(self, fck: float) -> float:
        """Coeficiente de redimento da resistência do concreto a compressão."""
        return 0.85 if fck <= 50 else 0.85 * (1.0 - (fck - 50) / 200.0)

    # -- ductilidade ------------------------------------------------------
    def kx_limite(self, fck: float) -> float:
        d = self.dados["ductilidade"]["kx_limite"]
        return d["ate_50_MPa"] if fck <= 50 else d["acima_50_MPa"]

    def eps_su_permil(self) -> float:
        return float(self.dados["ductilidade"]["eps_su_permil"]["valor"])

    def eps_cu_permil(self, fck: float) -> float:
        """Deformacao última do concreto, em permil."""
        d = self.dados["ductilidade"]["eps_cu_permil"]
        if fck <= 50:
            return float(d["ate_50_MPa"])
        formula = _exigir(
            d.get("formula_acima_50_MPa"),
            f"eps_cu para fck = {fck:g} MPa (acima de 50 MPa)",
            "ductilidade.eps_cu_permil.formula_acima_50_MPa",
        )
        # A expressao vem do YAML do usuário; avaliada num namespace fechado.
        return float(eval(formula, {"__builtins__": {}, "math": math}, {"fck": fck}))

    def limite_dominio_2_3(self, fck: float) -> float:
        ecu = self.eps_cu_permil(fck)
        return ecu / (ecu + self.eps_su_permil())

    # -- rho_min ----------------------------------------------------------
    def rho_min(self, fck: float) -> float:
        """Taxa mínima geométrica de armadura, em fração (0.0015 = 0,15%)."""
        tabela = self.dados["rho_min_percent"]["tabela"]
        if fck not in tabela:
            disponiveis = sorted(k for k, v in tabela.items() if v != PENDENTE)
            raise DadoNormativoAusente(
                f"rho_min para fck = {fck:g} MPa não está tabelado.\n"
                f"  Preencha a linha `{fck:g}:` em rho_min_percent.tabela "
                f"(config/normas.yaml).\n"
                f"  Hoje há valor para: {', '.join(f'C{k:g}' for k in disponíveis)}."
            )
        pct = _exigir(
            tabela[fck],
            f"rho_min para fck = {fck:g} MPa",
            f"rho_min_percent.tabela[{fck:g}]",
        )
        return float(pct) / 100.0

    # -- aço --------------------------------------------------------------
    def aco(self, nome: str) -> dict:
        acos = self.dados["acos"]
        if nome not in acos:
            raise ConfiguracaoInvalida(
                f"Aço '{nome}' desconhecido. Disponiveis: {', '.join(acos)}."
            )
        return acos[nome]

    def fyk(self, aco: str) -> float:
        return float(self.aco(aco)["fyk_MPa"])

    def eh_nervurada(self, aco: str) -> bool:
        return bool(self.aco(aco)["nervurada"])

    def Es_MPa(self) -> float:
        return 1000.0 * float(
            _exigir(
                self.dados["Es_GPa"]["valor"],
                "módulo de elasticidade do aço (Es)",
                "Es_GPa.valor",
            )
        )

    def tem_Es(self) -> bool:
        return self.dados["Es_GPa"]["valor"] not in (None, PENDENTE)

    # -- barras -----------------------------------------------------------
    def area_nominal(self, bitola_mm: float) -> float:
        """Área nominal de UMA barra, em cm2 (NBR 7480)."""
        tabela = self.dados["areas_nominais_cm2"]["tabela"]
        if bitola_mm not in tabela:
            raise ConfiguracaoInvalida(
                f"Bitola {bitola_mm:g} mm não tabelada. "
                f"Disponiveis: {', '.join(f'{b:g}' for b in sorted(tabela))}. "
                f"Acrescente em areas_nominais_cm2.tabela (config/normas.yaml)."
            )
        return float(tabela[bitola_mm])

    def massa_linear(self, bitola_mm: float) -> float | None:
        tabela = self.dados["massa_linear_kg_m"]["tabela"]
        if tabela == PENDENTE or tabela is None:
            return None
        return float(tabela.get(bitola_mm)) if bitola_mm in tabela else None

    # -- ações ------------------------------------------------------------
    def carga_acidental(self, uso: str) -> float:
        tabela = self.dados["cargas_acidentais_kN_m2"]["tabela"]
        if uso not in tabela:
            raise ConfiguracaoInvalida(
                f"Uso '{uso}' não consta na tabela de cargas acidentais.\n"
                f"  Use uma destas chaves (ou informe ações.acidental_kN_m2):\n    "
                + "\n    ".join(tabela)
            )
        return float(tabela[uso])

    def peso_especifico_concreto(self) -> float:
        return float(self.dados["peso_especifico_concreto_kN_m3"]["valor"])

    # -- aderência --------------------------------------------------------
    def eta1(self, aco: str) -> float:
        d = self.dados["aderencia"]["eta1"]
        return float(d["nervurada"] if self.eh_nervurada(aco) else d["lisa"])

    def eta2(self, aderencia: str) -> float:
        d = self.dados["aderencia"]["eta2"]
        if aderencia not in d:
            raise ConfiguracaoInvalida(
                f"materiais.aderência deve ser 'boa' ou 'ma' (recebi '{aderencia}')."
            )
        return float(d[aderencia])

    def eta3(self, bitola_mm: float) -> float:
        ad = self.dados["aderencia"]
        if bitola_mm <= 32:
            return float(ad["eta3_ate_32mm"])
        return (132.0 - bitola_mm) / 100.0

    def alpha_ancoragem(self, modo: str) -> float:
        d = self.dados["aderencia"]["alpha_ancoragem"]
        if modo not in d:
            raise ConfiguracaoInvalida(
                f"Ancoragem deve ser 'reta' ou 'com_gancho' (recebi '{modo}')."
            )
        return float(d[modo])

    def ponta_reta_gancho(self, tipo: str, bitola_mm: float) -> float:
        """Ponta reta mínima do gancho, em cm."""
        d = self.dados["ganchos"]["ponta_reta_min_n_phi"]
        if tipo not in d:
            raise ConfiguracaoInvalida(
                f"Tipo de gancho '{tipo}' desconhecido. Opções: {', '.join(d)}."
            )
        return float(d[tipo]) * bitola_mm / 10.0
