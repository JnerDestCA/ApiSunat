from __future__ import annotations
from typing import Any


class ComprobanteService:
    async def emitir_boleta(self, dto: Any) -> Any:
        raise NotImplementedError

    async def emitir_factura(self, dto: Any) -> Any:
        raise NotImplementedError

    async def consultar(self, id: str) -> Any:
        raise NotImplementedError

    async def anular(self, id: str, motivo: str) -> Any:
        raise NotImplementedError
