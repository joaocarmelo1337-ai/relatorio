"""Casos de teste do exemplo da apostila.

Os cinco valores conferidos a mao pelo usuario são:
    x = 3,66 cm | Kx = 0,407 | As = 10,22 cm2/m | lb = 37,7 cm
    lb,nec = 25,7 cm com gancho

Eles formam a cadeia flexao -> ancoragem, cuja ENTRADA e' Md = 33,50 kN.m.
Por isso a classe `TestValoresConferidos` alimenta o motor com esse Md
diretamente. A cadeia completa (ações -> Mk -> Md) e' testada a parte, em
`TestCadeiaCompleta`, onde Md sai 33,52 kN.m: a diferenca de 0,02 kN.m vem do
arredondamento do cálculo manual original, que fechou Mk em 23,93 kN.m.
"""
import math

import pytest

from engine import calcular
from engine import ancoragem as mod_anc
from engine import flexao as mod_flex
from engine import geometria as mod_geo
from engine.flexao import SecaoInsuficiente
from engine.normas import ConfiguracaoInvalida, DadoNormativoAusente


# ===========================================================================
class TestValoresConferidos:
    """Md = 33,50 kN.m, C25, CA-50, d = 9,0 cm, bw = 100 cm."""

    @pytest.fixture
    def flex(self, cfg, normas):
        geo = mod_geo.construir(cfg)
        return mod_flex.calcular(33.50, geo, cfg, normas)

    def test_altura_util(self, cfg):
        assert mod_geo.construir(cfg).d == pytest.approx(9.0)

    def test_x_linha_neutra(self, flex):
        assert flex.x == pytest.approx(3.66, abs=5e-3)

    def test_kx(self, flex):
        assert flex.kx == pytest.approx(0.407, abs=5e-4)

    def test_As(self, flex):
        assert flex.As_por_metro == pytest.approx(10.22, abs=5e-3)

    def test_dominio_3(self, flex):
        assert flex.dominio == "3"
        assert flex.ductil

    def test_deformacao_do_aco(self, flex):
        """eps_s = 3,5 permil x (d - x)/x, conferido em 5,11 permil."""
        assert flex.eps_s == pytest.approx(5.11, abs=1e-2)
        assert flex.eps_s < 10.0

    def test_momento_limite_da_secao(self, flex):
        """(alpha_c/2) x bw x d2 x fcd = 6148 kN.cm, citado na seção 5.1."""
        assert flex.Mlim == pytest.approx(6148, abs=1.0)

    # -- ancoragem --------------------------------------------------------
    @pytest.fixture
    def anc(self, cfg, normas, flex):
        As_ef = 100.0 / 7.5 * normas.area_nominal(10.0)
        return {
            m: mod_anc.calcular(10.0, m, flex.As_por_metro, As_ef, cfg, normas)
            for m in ("reta", "com_gancho")
        }

    def test_fctd(self, anc):
        assert anc["reta"].fctd == pytest.approx(0.1282, abs=5e-5)

    def test_fbd(self, anc):
        assert anc["reta"].fbd == pytest.approx(0.2886, abs=5e-5)

    def test_fbd_nao_e_fctd(self, anc):
        """O erro classico: usar fctd no lugar de fbd da 2,25x a mais."""
        assert anc["reta"].fbd / anc["reta"].fctd == pytest.approx(2.25)

    def test_lb(self, anc):
        assert anc["reta"].lb == pytest.approx(37.7, abs=5e-2)
        assert anc["reta"].lb_em_phi == pytest.approx(37.7, abs=5e-2)

    def test_lb_nec_com_gancho(self, anc):
        """O original registrou 25,7: e' 25,76 truncado, não arredondado
        (o par reto dele, 36,8, fecha exato). Dai a tolerancia de 0,1."""
        assert anc["com_gancho"].lb_nec == pytest.approx(25.7, abs=0.1)
        assert anc["com_gancho"].lb_nec == pytest.approx(
            0.7 * anc["reta"].lb_nec, rel=1e-9
        )

    def test_lb_nec_reta(self, anc):
        assert anc["reta"].lb_nec == pytest.approx(36.8, abs=5e-2)

    def test_lb_min_nao_governa(self, anc):
        """maior entre 0,3.lb (11,3), 10ø (10) e 10 cm - atendido nos dois casos."""
        assert anc["reta"].lb_min == pytest.approx(11.3, abs=5e-2)
        assert not anc["reta"].governa_minimo
        assert not anc["com_gancho"].governa_minimo


# ===========================================================================
class TestCadeiaCompleta:
    """Do config até a barra, sem número digitado no meio."""

    @pytest.fixture
    def r(self, cfg):
        return calcular(cfg)

    def test_geometria(self, r):
        assert r.geo.alpha_graus == pytest.approx(33.45, abs=1e-2)
        assert r.geo.h1 == pytest.approx(14.38, abs=5e-3)
        assert r.geo.hm == pytest.approx(24.0)
        assert r.geo.vao_total == pytest.approx(464.0)
        assert r.geo.subida == pytest.approx(148.0)

    def test_cargas(self, r):
        assert r.cargas.pp_patamar == pytest.approx(3.0)
        assert r.cargas.pp_lance == pytest.approx(6.0)
        assert r.cargas.acidental == pytest.approx(2.5)
        assert r.cargas.q_lance == pytest.approx(9.7)
        assert r.cargas.q_patamar == pytest.approx(6.7)

    def test_momento_bate_com_o_calculo_manual_original(self, r):
        """O original fechou Mk = 23,93; o motor da 23,94 (arredondamento)."""
        assert r.esforcos.Mk == pytest.approx(23.93, abs=2e-2)
        assert r.esforcos.Md == pytest.approx(33.50, abs=3e-2)

    def test_momento_maximo_no_meio_do_vao(self, r):
        assert r.esforcos.x_Mk_max == pytest.approx(r.geo.vao_total / 200.0, abs=1e-3)

    def test_equilibrio_do_diagrama(self, r):
        """M e V tem de zerar nos apoios e V(x) = dM/dx."""
        e = r.esforcos
        assert e.M(0.0) == pytest.approx(0.0, abs=1e-9)
        assert e.M(e.vao) == pytest.approx(0.0, abs=1e-6)
        assert e.R_a + e.R_b == pytest.approx(e.carga_total)
        h = 1e-4
        x = 1.0
        assert (e.M(x + h) - e.M(x - h)) / (2 * h) == pytest.approx(e.V(x), abs=1e-3)

    def test_flexao_com_o_momento_calculado(self, r):
        assert r.flexao.x == pytest.approx(3.66, abs=1e-2)
        assert r.flexao.kx == pytest.approx(0.407, abs=1e-3)
        assert r.flexao.As_por_metro == pytest.approx(10.23, abs=1e-2)

    def test_As_efetiva_cobre_a_calculada(self, r):
        assert r.armadura["As_ef"] == pytest.approx(10.47, abs=5e-3)
        assert r.armadura["As_ef"] >= r.armadura["As_calc"]

    def test_armadura_minima_e_distribuicao(self, r):
        assert r.armadura["As_min"] == pytest.approx(1.80, abs=5e-3)
        assert r.armadura["As_dist"] == pytest.approx(0.20 * r.armadura["As_calc"])
        assert "principal" in r.armadura["governa_dist"]

    def test_comparacao_de_bitolas(self, r):
        c10 = next(c for c in r.armadura["comparacao_bitolas"] if c["bitola"] == 10.0)
        assert c10["espacamento"] == pytest.approx(7.7, abs=5e-2)


# ===========================================================================
class TestPosicoesDeBarra:
    @pytest.fixture
    def det(self, cfg):
        return calcular(cfg).detalhamento

    def test_toda_posicao_tem_descricao(self, det):
        """Regra do projeto: o codigo N-x nunca viaja sozinho."""
        for p in det.posicoes:
            assert p.descricao, f"{p.codigo} sem descrição"
            assert len(p.descricao) > 10
            assert p.codigo in p.rotulo and p.descricao in p.rotulo
            assert p.descricao in p.chamada

    def test_toda_posicao_tem_formatos_alternativos(self, det):
        """Regra do projeto: sempre mais de um formato, com quando-usar."""
        for p in det.posicoes:
            alts = p.formatos_alternativos
            assert len(alts) >= 2, f"{p.codigo} tem só um formato"
            assert any(f.id == p.formato_adotado for f in alts)
            for f in alts:
                assert f.quando_usar and f.vantagem and f.desvantagem

    def test_a_positiva_cobre_o_vao_inteiro(self, det, cfg):
        """N1 + N2 + N3 tem de varrer de apoio a apoio, com sobreposição."""
        geo = mod_geo.construir(cfg)
        n1, n2, n3 = (det.por_codigo(c) for c in ("N1", "N2", "N3"))
        assert n1.x_ini == pytest.approx(geo.c)
        assert n3.x_fim == pytest.approx(geo.x3 - geo.c)
        assert n2.x_ini < n1.x_fim, "vão descoberto entre N1 e N2"
        assert n3.x_ini < n2.x_fim, "vão descoberto entre N2 e N3"

    def test_traspasse_vale_pelo_menos_lb_nec(self, cfg):
        r = calcular(cfg)
        det, geo = r.detalhamento, r.geo
        lb = r.anc_gancho.lb_nec
        n1, n2, n3 = (det.por_codigo(c) for c in ("N1", "N2", "N3"))
        from engine.barras import _dev
        assert _dev(geo, n2.x_ini, n1.x_fim) >= lb - 0.1
        assert _dev(geo, n3.x_ini, n2.x_fim) >= lb - 0.1

    def test_emendas_longe_do_momento_maximo(self, det):
        assert det.emenda_longe_do_maximo

    def test_gancho_e_limitado_pela_espessura(self, det):
        """h - 2c = 7 cm, menor que o 8ø da norma: o motor tem de avisar."""
        assert det.gancho_cm == pytest.approx(7.0)
        assert det.gancho_normativo_cm == pytest.approx(8.0)
        assert not det.gancho_cabe

    def test_distribuicao_fica_acima_da_principal(self, det):
        assert det.por_codigo("N4").offset_cm > det.por_codigo("N1").offset_cm

    def test_n6_fica_na_face_superior(self, det):
        assert det.por_codigo("N6").face == "superior"
        assert det.por_codigo("N6").quantidade == 4

    def test_comprimento_soma_reto_mais_ganchos(self, det):
        n1 = det.por_codigo("N1")
        assert n1.comprimento_cm == pytest.approx(n1.trecho_reto_cm + 7.0)


# ===========================================================================
class TestParametrizacao:
    """Mudar o config tem de mudar TUDO, sem editar codigo."""

    def test_mais_degraus_alonga_o_vao_e_o_aco(self, cfg):
        cfg["armaduras"]["principal"]["espacamento_cm"] = "auto"
        cfg["armaduras"]["distribuicao"]["espacamento_cm"] = "auto"
        base = calcular(cfg)
        cfg["geometria"]["n_degraus"] = 10
        alt = calcular(cfg)
        assert alt.geo.vao_total > base.geo.vao_total
        assert alt.esforcos.Mk > base.esforcos.Mk
        assert alt.flexao.As_por_metro > base.flexao.As_por_metro
        assert alt.detalhamento.por_codigo("N2").comprimento_cm > \
            base.detalhamento.por_codigo("N2").comprimento_cm

    def test_espessura_maior_reduz_kx(self, cfg):
        base = calcular(cfg)
        cfg["geometria"]["espessura_h"] = 15.0
        cfg["armaduras"]["principal"]["espacamento_cm"] = 9.0
        alt = calcular(cfg)
        assert alt.geo.d > base.geo.d
        assert alt.flexao.kx < base.flexao.kx

    def test_fck_maior_muda_lambda_alpha_c_e_o_x(self, cfg, normas):
        cfg["materiais"]["fck"] = 40
        r = calcular(cfg)
        assert r.flexao.lam == 0.80 and r.flexao.alpha_c == 0.85
        assert r.flexao.x < 3.66          # concreto mais forte, LN mais alta
        assert r.anc_reta.lb < 37.7       # e aderência melhor

    def test_uso_diferente_muda_a_carga_acidental(self, cfg):
        cfg["armaduras"]["principal"]["espacamento_cm"] = "auto"
        cfg["armaduras"]["distribuicao"]["espacamento_cm"] = "auto"
        cfg["acoes"]["uso"] = "Cinemas, centros comerciais, shopping"
        r = calcular(cfg)
        assert r.cargas.acidental == 4.0
        assert r.esforcos.Mk > 23.93

    def test_mk_pinado_sobrepoe_o_calculado(self, cfg):
        cfg["esforcos"]["momento_caracteristico_kNm"] = 23.93
        r = calcular(cfg)
        assert r.esforcos.Mk == 23.93
        assert r.esforcos.foi_pinado
        assert r.flexao.As_por_metro == pytest.approx(10.22, abs=1e-2)
        assert any("PINADO" in a for a in r.avisos)

    def test_bitola_maior_muda_espacamento_e_ancoragem(self, cfg):
        cfg["armaduras"]["principal"]["bitola_mm"] = 12.5
        cfg["armaduras"]["principal"]["espacamento_cm"] = 11.0
        r = calcular(cfg)
        assert r.anc_reta.lb > 37.7       # lb cresce com a bitola
        assert r.detalhamento.por_codigo("N1").bitola_mm == 12.5

    def test_calcular_nao_mutila_o_config_do_chamador(self, cfg):
        cfg["armaduras"]["principal"]["espacamento_cm"] = "auto"
        calcular(cfg)
        assert cfg["armaduras"]["principal"]["espacamento_cm"] == "auto"

    def test_espacamento_auto_escolhe_e_cobre(self, cfg):
        cfg["armaduras"]["principal"]["espacamento_cm"] = "auto"
        r = calcular(cfg)
        esp = r.cfg["armaduras"]["principal"]["espacamento_cm"]
        assert esp == pytest.approx(7.5)       # o mesmo que o projeto adotou
        assert r.armadura["As_ef"] >= r.armadura["As_calc"]

    def test_espacamento_auto_reage_a_mudanca_de_carga(self, cfg):
        cfg["armaduras"]["principal"]["espacamento_cm"] = "auto"
        cfg["armaduras"]["distribuicao"]["espacamento_cm"] = "auto"
        leve = calcular(cfg)
        cfg["acoes"]["uso"] = "Centros de exposição e de convenções"
        pesado = calcular(cfg)
        assert pesado.cfg["armaduras"]["principal"]["espacamento_cm"] < \
            leve.cfg["armaduras"]["principal"]["espacamento_cm"]


# ===========================================================================
class TestFalhasExplicitas:
    """O motor recusa em vez de entregar número errado."""

    def test_fck_sem_rho_min_tabelado(self, cfg):
        cfg["materiais"]["fck"] = 35
        with pytest.raises(DadoNormativoAusente, match="rho_min"):
            calcular(cfg)

    def test_fck_acima_de_50_sem_eps_cu(self, cfg):
        cfg["materiais"]["fck"] = 60
        with pytest.raises(DadoNormativoAusente, match="eps_cu"):
            calcular(cfg)

    def test_armadura_adotada_insuficiente(self, cfg):
        cfg["armaduras"]["principal"]["espacamento_cm"] = 20.0
        with pytest.raises(ConfiguracaoInvalida, match="não cobre"):
            calcular(cfg)

    def test_laje_fina_demais_para_o_momento(self, cfg):
        cfg["geometria"]["espessura_h"] = 8.0
        with pytest.raises((SecaoInsuficiente, ConfiguracaoInvalida)):
            calcular(cfg)

    def test_esquema_nao_implementado(self, cfg):
        cfg["geometria"]["esquema"] = "engastado"
        with pytest.raises(ConfiguracaoInvalida, match="não implementado"):
            calcular(cfg)

    def test_uso_fora_da_tabela(self, cfg):
        cfg["acoes"]["uso"] = "Heliponto"
        with pytest.raises(ConfiguracaoInvalida, match="não consta"):
            calcular(cfg)

    def test_bitola_fora_da_nbr7480(self, cfg):
        cfg["armaduras"]["principal"]["bitola_mm"] = 11.0
        with pytest.raises(ConfiguracaoInvalida, match="não tabelada"):
            calcular(cfg)


# ===========================================================================
class TestAvisos:
    def test_blondel_fora_da_faixa_gera_aviso(self, cfg):
        r = calcular(cfg)   # s + 2e = 65 > 64
        assert any("Blondel" in a for a in r.avisos)

    def test_blondel_dentro_da_faixa_nao_gera_aviso(self, cfg):
        cfg["geometria"]["piso_s"] = 27.0
        cfg["geometria"]["espelho_e"] = 17.5
        r = calcular(cfg)
        assert not any("Blondel" in a for a in r.avisos)
