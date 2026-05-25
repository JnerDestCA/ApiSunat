from __future__ import annotations
from typing import Dict, Optional
from app.domain.entities.comprobante import Comprobante
from app.domain.ports.outbound.comprobante_repo import ComprobanteRepository


class MemoryRepository(ComprobanteRepository):
    def __init__(self):
        self._data: Dict[str, Comprobante] = {}

    async def save(self, comprobante: Comprobante) -> Comprobante:
        self._data[comprobante.id] = comprobante
        return comprobante

    async def find_by_id(self, id: str) -> Optional[Comprobante]:
        return self._data.get(id)

    async def find_by_serie_correlativo(
        self, ruc_emisor: str, serie: str, correlativo: int, tipo: str
    ) -> Optional[Comprobante]:
        for c in self._data.values():
            if (
                str(c.ruc_emisor) == ruc_emisor
                and c.serie_correlativo.serie == serie
                and c.serie_correlativo.correlativo == correlativo
                and c.tipo.value == tipo
            ):
                return c
        return None

    async def update(self, comprobante: Comprobante) -> Comprobante:
        self._data[comprobante.id] = comprobante
        return comprobante

    async def delete(self, id: str) -> None:
        self._data.pop(id, None)
