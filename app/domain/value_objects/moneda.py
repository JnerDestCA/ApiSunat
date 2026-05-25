from enum import Enum


class Moneda(Enum):
    PEN = "PEN"
    USD = "USD"
    EUR = "EUR"

    @classmethod
    def from_str(cls, value: str) -> "Moneda":
        try:
            return cls(value.upper())
        except ValueError:
            raise ValueError(f"Moneda inválida: {value}. Opciones: {[m.value for m in cls]}")
