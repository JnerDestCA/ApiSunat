from __future__ import annotations
from decimal import Decimal

from app.application.dtos.response_dto import (
    ComprobanteDetalleResponse,
    ItemResponseDTO,
)
from app.domain.entities.boleta import Boleta
from app.domain.entities.comprobante import Comprobante
from app.domain.entities.factura import Factura
from app.domain.ports.inbound.comprobante_service import ComprobanteService
from app.domain.ports.outbound.comprobante_repo import ComprobanteRepository


class ConsultarComprobanteUseCase(ComprobanteService):
    def __init__(self, repo: ComprobanteRepository):
        self._repo = repo

    async def consultar(self, id: str) -> ComprobanteDetalleResponse:
        comprobante = await self._repo.find_by_id(id)
        if comprobante is None:
            raise ValueError(f"Comprobante {id} no encontrado")
        return self._to_response(comprobante)

    async def emitir_boleta(self, dto: object) -> object:
        raise NotImplementedError

    async def emitir_factura(self, dto: object) -> object:
        raise NotImplementedError

    async def anular(self, id: str, motivo: str) -> object:
        raise NotImplementedError

    @staticmethod
    def _to_response(c: Comprobante) -> ComprobanteDetalleResponse:
        items = [
            ItemResponseDTO(
                descripcion=i.descripcion,
                cantidad=i.cantidad,
                precio_unitario=i.precio_unitario,
                igv_porcentaje=i.igv_porcentaje,
                unidad_medida=i.unidad_medida,
                subtotal=i.subtotal,
                igv=i.igv,
                total=i.total,
            )
            for i in c.items
        ]

        ruc_receptor = None
        razon_social = None
        if isinstance(c, Factura):
            ruc_receptor = str(c.ruc_receptor) if c.ruc_receptor else None
            razon_social = c.razon_social_receptor

        tipo_doc_cliente = None
        num_doc_cliente = None
        nombre_cliente = None
        if isinstance(c, (Boleta, Factura)):
            tipo_doc_cliente = getattr(c, "tipo_doc_cliente", None)
            num_doc_cliente = getattr(c, "num_doc_cliente", None)
            nombre_cliente = getattr(c, "nombre_cliente", None)

        return ComprobanteDetalleResponse(
            id=c.id,
            ruc_emisor=str(c.ruc_emisor),
            serie=c.serie_correlativo.serie,
            correlativo=c.serie_correlativo.correlativo,
            tipo=c.tipo.value,
            fecha_emision=c.fecha_emision,
            moneda=c.moneda.value,
            estado=c.estado.value,
            items=items,
            tipo_doc_cliente=tipo_doc_cliente,
            num_doc_cliente=num_doc_cliente,
            nombre_cliente=nombre_cliente,
            ruc_receptor=ruc_receptor,
            razon_social_receptor=razon_social,
            xml_firmado_b64=c.xml_firmado_b64,
            hash_cpe=c.hash_cpe,
            cdr_codigo=c.cdr_codigo,
            cdr_descripcion=c.cdr_descripcion,
            cdr_observaciones=c.cdr_observaciones,
            motivo_anulacion=c.motivo_anulacion,
            total_subtotal=c.total_subtotal,
            total_igv=c.total_igv,
            total=c.total,
        )
