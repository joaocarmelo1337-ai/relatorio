"""As formulas de lambda/alpha_c tem de reproduzir a tabela dos arquivos
originais, e todo PENDENTE tem de falhar alto em vez de virar chute."""
import pytest

from engine.normas import DadoNormativoAusente, Normas


def test_lambda_e_alpha_c_reproduzem_a_tabela_original(normas):
    """A tabela da seção 5.1 do build.js, linha por linha.

    Tolerancia de 1e-3 porque a tabela original traz 3 casas decimais: para
    fck = 60 a formula da 0,8075 e a tabela arredondou para 0,808.
    """
    for fck, lam_tab, ac_tab in normas["bloco_retangular"]["tabela"]:
        assert normas.lambda_(fck) == pytest.approx(lam_tab, abs=1e-3)
        assert normas.alpha_c(fck) == pytest.approx(ac_tab, abs=1e-3)


def test_ate_50_MPa_os_coeficientes_sao_os_classicos(normas):
    for fck in (20, 25, 30, 40, 50):
        assert normas.lambda_(fck) == 0.80
        assert normas.alpha_c(fck) == 0.85
        # os famosos 1,25 e 0,425 da versao simplificada
        assert 1 / normas.lambda_(fck) == pytest.approx(1.25)
        assert normas.alpha_c(fck) / 2 == pytest.approx(0.425)


def test_acima_de_50_MPa_os_coeficientes_mudam(normas):
    """O motor NÃO fixa 0,425 e 1,25: acima de 50 MPa eles caem."""
    assert normas.lambda_(60) < normas.lambda_(50)
    assert normas.alpha_c(60) < normas.alpha_c(50)
    assert 1 / normas.lambda_(90) == pytest.approx(1.4286, abs=1e-4)
    assert normas.alpha_c(90) / 2 == pytest.approx(0.340, abs=5e-4)


def test_kx_limite_cai_acima_de_50(normas):
    assert normas.kx_limite(50) == 0.45
    assert normas.kx_limite(60) == 0.35


def test_limite_dominio_2_3_bate_com_o_0259_da_figura(normas):
    assert normas.limite_dominio_2_3(25) == pytest.approx(0.259, abs=5e-4)


def test_eps_cu_ate_50_MPa(normas):
    for fck in (20, 25, 30, 40, 50):
        assert normas.eps_cu_permil(fck) == 3.5


def test_eps_cu_emenda_com_o_ramo_de_baixo_em_50_MPa(normas):
    """A prova de que a expressão informada para fck > 50 é a certa.

    A fórmula não vale em 50 MPa (lá manda o outro ramo), mas o limite dela
    quando fck tende a 50 tem de reencontrar o 3,5 permil dos arquivos
    originais. Dá 3,496: é o mesmo 3,5 arredondado. Se a expressão estivesse
    errada, os dois ramos não emendariam.
    """
    formula = normas["ductilidade"]["eps_cu_permil"]["formula_acima_50_MPa"]
    em_50 = eval(formula, {"__builtins__": {}}, {"fck": 50.0})
    assert em_50 == pytest.approx(3.5, abs=5e-3)


def test_eps_cu_acima_de_50_cai_com_o_fck(normas):
    valores = [normas.eps_cu_permil(f) for f in (55, 60, 70, 80, 90)]
    assert valores == sorted(valores, reverse=True)
    assert normas.eps_cu_permil(90) == pytest.approx(2.6, abs=1e-9)
    assert normas.eps_cu_permil(70) == pytest.approx(2.656, abs=5e-4)


def test_limite_dominio_2_3_acompanha_o_eps_cu(normas):
    """Não é um 0,259 fixo: ele anda junto com a deformação última."""
    assert normas.limite_dominio_2_3(25) == pytest.approx(0.259, abs=5e-4)
    assert normas.limite_dominio_2_3(90) < normas.limite_dominio_2_3(25)
    assert normas.limite_dominio_2_3(90) == pytest.approx(2.6 / 12.6, abs=1e-6)


def test_rho_min_pendente_falha_alto(normas):
    assert normas.rho_min(25) == pytest.approx(0.0015)
    assert normas.rho_min(40) == pytest.approx(0.00179)
    assert normas.rho_min(90) == pytest.approx(0.00256)
    with pytest.raises(DadoNormativoAusente, match="rho_min"):
        normas.rho_min(35)


def test_rho_min_nao_interpola(normas):
    """Se interpolasse, C35 daria ~0,165%. Tem de levantar erro em vez disso."""
    with pytest.raises(DadoNormativoAusente):
        normas.rho_min(35)


def test_eta1_depende_de_ser_nervurada(normas):
    assert normas.eta1("CA-50") == 2.25
    assert normas.eta1("CA-60") == 1.00
    assert normas.eta1("CA-25") == 1.00


def test_eta3_muda_acima_de_32mm(normas):
    assert normas.eta3(10.0) == 1.00
    assert normas.eta3(40.0) == pytest.approx(0.92)


def test_area_nominal_vem_da_tabela_nbr7480(normas):
    assert normas.area_nominal(10.0) == 0.785
    assert normas.area_nominal(12.5) == 1.227


def test_areas_nominais_sao_pi_phi2_sobre_4(normas):
    """Cada área tabelada e' a área geométrica da barra nominal."""
    import math
    for bitola, area in normas["areas_nominais_cm2"]["tabela"].items():
        phi_cm = bitola / 10.0
        assert area == pytest.approx(math.pi * phi_cm ** 2 / 4, abs=5e-4)


def test_areas_nominais_batem_com_a_tabela_de_2_casas_do_original(normas):
    """A tabela da seção 5.4 do build.js, arredondada a 2 casas."""
    original_2_casas = {5.0: 0.20, 6.3: 0.31, 8.0: 0.50, 10.0: 0.79,
                        12.5: 1.23, 16.0: 2.01, 20.0: 3.14}
    for bitola, esperado in original_2_casas.items():
        assert round(normas.area_nominal(bitola), 2) == esperado
