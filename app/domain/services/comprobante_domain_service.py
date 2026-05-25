from __future__ import annotations
from decimal import Decimal
from typing import List

from app.domain.entities.comprobante import Comprobante, Item


class ComprobanteDomainService:
    @staticmethod
    def calcular_totales(items: List[Item]) -> dict:
        subtotal = sum((item.subtotal for item in items), Decimal("0"))
        igv = sum((item.igv for item in items), Decimal("0"))
        total = sum((item.total for item in items), Decimal("0"))
        return {
            "subtotal": subtotal.quantize(Decimal("0.01")),
            "igv": igv.quantize(Decimal("0.01")),
            "total": total.quantize(Decimal("0.01")),
        }

    @staticmethod
    def validar_montos(comprobante: Comprobante) -> None:
        totales = ComprobanteDomainService.calcular_totales(comprobante.items)
        if totales["total"] <= 0:
            raise ValueError("El total del comprobante debe ser mayor a 0")
        for item in comprobante.items:
            if item.precio_unitario < 0:
                raise ValueError(
                    f"Precio unitario negativo en item: {item.descripcion}"
                )
