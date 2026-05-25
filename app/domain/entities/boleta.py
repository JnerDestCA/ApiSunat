from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from app.domain.entities.comprobante import Comprobante, TipoComprobante


@dataclass
class Boleta(Comprobante):
    tipo_doc_cliente: Optional[str] = None
    num_doc_cliente: Optional[str] = None
    nombre_cliente: Optional[str] = None

    def __post_init__(self):
        super().__post_init__()
        object.__setattr__(self, "tipo", TipoComprobante.BOLETA)
