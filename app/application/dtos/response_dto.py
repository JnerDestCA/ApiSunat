from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


@dataclass
class ItemResponseDTO:
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    igv_porcentaje: Decimal
    unidad_medida: str
    subtotal: Decimal
    igv: Decimal
    total: Decimal


@dataclass
class ComprobanteDetalleResponse:
    id: str
    ruc_emisor: str
    serie: str
    correlativo: int
    tipo: str
    fecha_emision: datetime
    moneda: str
    estado: str
    items: List[ItemResponseDTO]
    tipo_doc_cliente: Optional[str] = None
    num_doc_cliente: Optional[str] = None
    nombre_cliente: Optional[str] = None
    ruc_receptor: Optional[str] = None
    razon_social_receptor: Optional[str] = None
    xml_firmado_b64: Optional[str] = None
    hash_cpe: Optional[str] = None
    cdr_codigo: Optional[str] = None
    cdr_descripcion: Optional[str] = None
    cdr_observaciones: Optional[str] = None
    motivo_anulacion: Optional[str] = None
    total_subtotal: Decimal = Decimal("0")
    total_igv: Decimal = Decimal("0")
    total: Decimal = Decimal("0")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class AnulacionResponse:
    id: str
    estado: str
    cdr_codigo: Optional[str] = None
    cdr_descripcion: Optional[str] = None
    cdr_observaciones: Optional[str] = None
    motivo: Optional[str] = None
