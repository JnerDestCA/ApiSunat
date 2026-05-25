from __future__ import annotations
from typing import Optional

from app.domain.entities.comprobante import Comprobante


class ComprobanteRepository:
    async def save(self, comprobante: Comprobante) -> Comprobante:
        raise NotImplementedError

    async def find_by_id(self, id: str) -> Optional[Comprobante]:
        raise NotImplementedError

    async def find_by_serie_correlativo(
        self, ruc_emisor: str, serie: str, correlativo: int, tipo: str
    ) -> Optional[Comprobante]:
        raise NotImplementedError

    async def update(self, comprobante: Comprobante) -> Comprobante:
        raise NotImplementedError

    async def delete(self, id: str) -> None:
        raise NotImplementedError
