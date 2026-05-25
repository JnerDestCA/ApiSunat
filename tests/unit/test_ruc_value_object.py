import pytest
from app.domain.value_objects.ruc import Ruc


class TestRucValueObject:
    def test_ruc_valido_11_digitos(self):
        ruc = Ruc("20123456786")
        assert ruc.value == "20123456786"

    def test_ruc_con_guiones_se_limpia(self):
        ruc = Ruc(" 20-123456786 ")
        assert ruc.value == "20123456786"

    def test_ruc_con_espacios_se_limpia(self):
        ruc = Ruc("  20123456786  ")
        assert ruc.value == "20123456786"

    def test_ruc_menos_de_11_digitos_lanza_error(self):
        with pytest.raises(ValueError, match="11 dígitos"):
            Ruc("12345678")

    def test_ruc_mas_de_11_digitos_lanza_error(self):
        with pytest.raises(ValueError, match="11 dígitos"):
            Ruc("123456789012")

    def test_ruc_vacio_lanza_error(self):
        with pytest.raises(ValueError, match="11 dígitos"):
            Ruc("")

    def test_ruc_con_letras_lanza_error(self):
        with pytest.raises(ValueError, match="11 dígitos"):
            Ruc("20A23456789")

    def test_ruc_digito_verificador_invalido_lanza_error(self):
        with pytest.raises(ValueError, match="dígito verificador inválido"):
            Ruc("20123456788")

    def test_ruc_digito_verificador_10_se_convierte_a_0(self):
        ruc = Ruc("36891234290")
        assert ruc.value == "36891234290"

    def test_ruc_digito_verificador_10_caso_invalido(self):
        with pytest.raises(ValueError, match="dígito verificador inválido"):
            Ruc("36891234291")

    def test_igualdad_entre_ruc(self):
        ruc1 = Ruc("20123456786")
        ruc2 = Ruc("20123456786")
        assert ruc1 == ruc2

    def test_ruc_como_string(self):
        ruc = Ruc("20123456786")
        assert str(ruc) == "20123456786"

    def test_ruc_hash(self):
        ruc1 = Ruc("20123456786")
        ruc2 = Ruc("20123456786")
        assert hash(ruc1) == hash(ruc2)
        assert len({ruc1, ruc2}) == 1

    def test_repr(self):
        ruc = Ruc("20123456786")
        assert repr(ruc) == "Ruc('20123456786')"
