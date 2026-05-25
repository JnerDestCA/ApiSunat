from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import uuid4

from app.domain.value_objects.moneda import Moneda
from app.domain.value_objects.ruc import Ruc
from app.domain.value_objects.serie_correlativo import SerieCorrelativo


class EstadoComprobante(Enum):
    EMITIDO = "EMITIDO"
    ANULADO = "ANULADO"
    RECHAZADO = "RECHAZADO"


class TipoComprobante(Enum):
    FACTURA = "01"
    BOLETA = "03"


@dataclass
class Item:
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    igv_porcentaje: Decimal = Decimal("0.18")
    unidad_medida: str = "NIU"

    def __post_init__(self):
        if self.cantidad <= 0:
            raise ValueError("Cantidad debe ser positiva")
        if self.precio_unitario < 0:
            raise ValueError("Precio unitario no puede ser negativo")
        if not self.descripcion.strip():
            raise ValueError("Descripción del item no puede estar vacía")

    @property
    def subtotal(self) -> Decimal:
        return (self.cantidad * self.precio_unitario).quantize(Decimal("0.01"))

    @property
    def igv(self) -> Decimal:
        return (self.subtotal * self.igv_porcentaje).quantize(Decimal("0.01"))

    @property
    def total(self) -> Decimal:
        return (self.subtotal + self.igv).quantize(Decimal("0.01"))


@dataclass
class Comprobante:
    ruc_emisor: Ruc
    serie_correlativo: SerieCorrelativo
    tipo: TipoComprobante = field(init=False)
    moneda: Moneda
    items: List[Item]
    id: str = field(default_factory=lambda: str(uuid4()))
    fecha_emision: datetime = field(default_factory=datetime.now)
    estado: EstadoComprobante = EstadoComprobante.EMITIDO
    xml_firmado_b64: Optional[str] = None
    hash_cpe: Optional[str] = None
    cdr_xml_b64: Optional[str] = None
    cdr_codigo: Optional[str] = None
    cdr_descripcion: Optional[str] = None
    cdr_observaciones: Optional[str] = None
    motivo_anulacion: Optional[str] = None

    def __post_init__(self):
        if not self.items:
            raise ValueError("Comprobante debe tener al menos un item")

    @property
    def total_igv(self) -> Decimal:
        return sum((item.igv for item in self.items), Decimal("0")).quantize(
            Decimal("0.01")
        )

    @property
    def total_subtotal(self) -> Decimal:
        return sum(
            (item.subtotal for item in self.items), Decimal("0")
        ).quantize(Decimal("0.01"))

    @property
    def total(self) -> Decimal:
        return sum(
            (item.total for item in self.items), Decimal("0")
        ).quantize(Decimal("0.01"))

    def anular(self, motivo: str) -> None:
        if self.estado != EstadoComprobante.EMITIDO:
            raise ValueError(
                f"No se puede anular un comprobante en estado {self.estado.value}"
            )
        if len(motivo) < 5 or len(motivo) > 100:
            raise ValueError("Motivo de anulación debe tener entre 5 y 100 caracteres")
        self.estado = EstadoComprobante.ANULADO
        self.motivo_anulacion = motivo

    def marcar_emitido(
        self,
        xml_firmado_b64: str,
        hash_cpe: str,
        cdr_xml_b64: str,
        cdr_codigo: str,
        cdr_descripcion: str,
        cdr_observaciones: Optional[str] = None,
    ) -> None:
        self.xml_firmado_b64 = xml_firmado_b64
        self.hash_cpe = hash_cpe
        self.cdr_xml_b64 = cdr_xml_b64
        self.cdr_codigo = cdr_codigo
        self.cdr_descripcion = cdr_descripcion
        self.cdr_observaciones = cdr_observaciones
