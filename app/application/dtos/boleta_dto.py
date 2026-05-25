from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional


@dataclass
class ItemDTO:
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    igv_porcentaje: Decimal = Decimal("0.18")
    unidad_medida: str = "NIU"


@dataclass
class EmitirBoletaRequest:
    ruc_emisor: str
    serie: str
    correlativo: int
    moneda: str
    items: List[ItemDTO]
    tipo_doc_cliente: Optional[str] = None
    num_doc_cliente: Optional[str] = None
    nombre_cliente: Optional[str] = None


@dataclass
class EmitirBoletaResponse:
    id: str
    xml_firmado_b64: Optional[str] = None
    hash_cpe: Optional[str] = None
    cdr_codigo: Optional[str] = None
    cdr_descripcion: Optional[str] = None
    cdr_observaciones: Optional[str] = None
    estado: str = "EMITIDO"
