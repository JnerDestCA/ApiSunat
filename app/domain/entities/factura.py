from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from app.domain.entities.comprobante import Comprobante, TipoComprobante
from app.domain.value_objects.ruc import Ruc


@dataclass
class Factura(Comprobante):
    ruc_receptor: Optional[Ruc] = None
    razon_social_receptor: Optional[str] = None
    tipo_doc_cliente: Optional[str] = None
    num_doc_cliente: Optional[str] = None
    nombre_cliente: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, "tipo", TipoComprobante.FACTURA)
        if self.ruc_receptor is None:
            raise ValueError("Factura requiere ruc_receptor")
        if not self.razon_social_receptor or not self.razon_social_receptor.strip():
            raise ValueError("Factura requiere razon_social_receptor")
