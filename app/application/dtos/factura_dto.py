from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional

from app.application.dtos.boleta_dto import ItemDTO


@dataclass
class EmitirFacturaRequest:
    ruc_emisor: str
    serie: str
    correlativo: int
    moneda: str
    items: List[ItemDTO]
    ruc_receptor: str
    razon_social_receptor: str
    tipo_doc_cliente: Optional[str] = None
    num_doc_cliente: Optional[str] = None
    nombre_cliente: Optional[str] = None


@dataclass
class EmitirFacturaResponse:
    id: str
    xml_firmado_b64: Optional[str] = None
    hash_cpe: Optional[str] = None
    cdr_codigo: Optional[str] = None
    cdr_descripcion: Optional[str] = None
    cdr_observaciones: Optional[str] = None
    estado: str = "EMITIDO"
