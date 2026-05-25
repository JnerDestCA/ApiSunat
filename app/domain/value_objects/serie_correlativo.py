from __future__ import annotations
import re


class SerieCorrelativo:
    _serie: str
    _correlativo: int

    def __init__(self, serie: str, correlativo: int):
        serie = serie.strip().upper()
        if not re.match(r"^[BF]\d{3}$", serie):
            raise ValueError(
                f"Serie inválida: {serie}. Debe ser F001-F999 o B001-B999"
            )
        if correlativo < 1 or correlativo > 99999999:
            raise ValueError(
                f"Correlativo inválido: {correlativo}. Debe estar entre 1 y 99999999"
            )
        self._serie = serie
        self._correlativo = correlativo

    @property
    def serie(self) -> str:
        return self._serie

    @property
    def correlativo(self) -> int:
        return self._correlativo

    @property
    def tipo(self) -> str:
        return "01" if self._serie.startswith("F") else "03"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, SerieCorrelativo):
            return NotImplemented
        return self._serie == other._serie and self._correlativo == other._correlativo

    def __hash__(self) -> int:
        return hash((self._serie, self._correlativo))

    def __str__(self) -> str:
        return f"{self._serie}-{self._correlativo:08d}"

    def __repr__(self) -> str:
        return f"SerieCorrelativo('{self._serie}', {self._correlativo})"
