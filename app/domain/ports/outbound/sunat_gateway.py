from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class CdrResponse:
    codigo_respuesta: str
    descripcion: str
    cdr_bytes: Optional[bytes] = None
    observaciones: Optional[str] = None


class SunatGateway:
    async def send_bill(self, zip_bytes: bytes, filename: str) -> CdrResponse:
        raise NotImplementedError

    async def get_status(self, ticket: str) -> CdrResponse:
        raise NotImplementedError

    async def send_summary(self, zip_bytes: bytes, filename: str) -> CdrResponse:
        raise NotImplementedError
