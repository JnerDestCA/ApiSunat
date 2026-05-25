from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import (
    get_anular_use_case,
    get_consultar_use_case,
)
from app.application.use_cases.anular_comprobante import AnularComprobanteUseCase
from app.application.use_cases.consultar_comprobante import ConsultarComprobanteUseCase

router = APIRouter(prefix="/api/v1/comprobantes", tags=["Comprobantes"])


class AnulacionBody(BaseModel):
    motivo: str = Field(..., min_length=5, max_length=100)


class AnulacionResponse(BaseModel):
    id: str
    estado: str
    cdr_codigo: Optional[str] = None
    cdr_descripcion: Optional[str] = None
    cdr_observaciones: Optional[str] = None
    motivo: Optional[str] = None


class ItemOut(BaseModel):
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    igv_porcentaje: Decimal
    unidad_medida: str
    subtotal: Decimal
    igv: Decimal
    total: Decimal


class ComprobanteDetalleOut(BaseModel):
    id: str
    ruc_emisor: str
    serie: str
    correlativo: int
    tipo: str
    fecha_emision: str
    moneda: str
    estado: str
    items: List[ItemOut]
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


@router.get("/health", tags=["Health"])
async def health():
    from app.config import settings

    return {
        "status": "ok",
        "sunat_env": "produccion" if settings.is_produccion else "beta",
    }


@router.get("/{id}", response_model=ComprobanteDetalleOut)
async def consultar_comprobante(
    id: str,
    use_case: ConsultarComprobanteUseCase = Depends(get_consultar_use_case),
):
    try:
        result = await use_case.consultar(id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    return ComprobanteDetalleOut(
        id=result.id,
        ruc_emisor=result.ruc_emisor,
        serie=result.serie,
        correlativo=result.correlativo,
        tipo=result.tipo,
        fecha_emision=result.fecha_emision.isoformat(),
        moneda=result.moneda,
        estado=result.estado,
        items=[
            ItemOut(
                descripcion=i.descripcion,
                cantidad=i.cantidad,
                precio_unitario=i.precio_unitario,
                igv_porcentaje=i.igv_porcentaje,
                unidad_medida=i.unidad_medida,
                subtotal=i.subtotal,
                igv=i.igv,
                total=i.total,
            )
            for i in result.items
        ],
        tipo_doc_cliente=result.tipo_doc_cliente,
        num_doc_cliente=result.num_doc_cliente,
        nombre_cliente=result.nombre_cliente,
        ruc_receptor=result.ruc_receptor,
        razon_social_receptor=result.razon_social_receptor,
        xml_firmado_b64=result.xml_firmado_b64,
        hash_cpe=result.hash_cpe,
        cdr_codigo=result.cdr_codigo,
        cdr_descripcion=result.cdr_descripcion,
        cdr_observaciones=result.cdr_observaciones,
        motivo_anulacion=result.motivo_anulacion,
        total_subtotal=result.total_subtotal,
        total_igv=result.total_igv,
        total=result.total,
    )


@router.post("/{id}/anular", response_model=AnulacionResponse)
async def anular_comprobante(
    id: str,
    body: AnulacionBody,
    use_case: AnularComprobanteUseCase = Depends(get_anular_use_case),
):
    try:
        result = await use_case.anular(id, body.motivo)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return AnulacionResponse(
        id=result.id,
        estado=result.estado,
        cdr_codigo=result.cdr_codigo,
        cdr_descripcion=result.cdr_descripcion,
        cdr_observaciones=result.cdr_observaciones,
        motivo=result.motivo,
    )
