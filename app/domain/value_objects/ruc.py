from __future__ import annotations
import re


class Ruc:
    _value: str

    def __init__(self, value: str):
        cleaned = re.sub(r"\D", "", value.strip())
        if len(cleaned) != 11:
            raise ValueError(f"RUC debe tener 11 dígitos, se recibieron {len(cleaned)}")
        if not self._validar_digito_verificador(cleaned):
            raise ValueError(f"RUC {cleaned} tiene dígito verificador inválido")
        self._value = cleaned

    @staticmethod
    def _validar_digito_verificador(ruc: str) -> bool:
        pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        suma = sum(int(ruc[i]) * pesos[i] for i in range(10))
        residuo = suma % 11
        digito_calculado = 11 - residuo
        if digito_calculado == 11:
            digito_calculado = 0
        elif digito_calculado == 10:
            digito_calculado = 0
        return digito_calculado == int(ruc[10])

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Ruc):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Ruc('{self._value}')"
