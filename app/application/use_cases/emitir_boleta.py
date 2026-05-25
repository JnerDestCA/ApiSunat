from __future__ import annotations
import hashlib
import base64
from datetime import datetime
from decimal import Decimal
from typing import List

from app.application.dtos.boleta_dto import (
    EmitirBoletaRequest,
    EmitirBoletaResponse,
    ItemDTO,
)
from app.domain.entities.boleta import Boleta
from app.domain.entities.comprobante import Item
from app.domain.ports.inbound.comprobante_service import ComprobanteService
from app.domain.ports.outbound.comprobante_repo import ComprobanteRepository
from app.domain.ports.outbound.sunat_gateway import SunatGateway
from app.domain.ports.outbound.xml_signer import XmlSigner
from app.domain.services.comprobante_domain_service import ComprobanteDomainService
from app.domain.value_objects.moneda import Moneda
from app.domain.value_objects.ruc import Ruc
from app.domain.value_objects.serie_correlativo import SerieCorrelativo
from app.infrastructure.xml.ubl21_builder import Ubl21Builder
from app.infrastructure.zip.zip_service import ZipService


class EmitirBoletaUseCase(ComprobanteService):
    def __init__(
        self,
        xml_signer: XmlSigner,
        sunat_gateway: SunatGateway,
        repo: ComprobanteRepository,
        ubl_builder: Ubl21Builder,
        zip_service: ZipService,
        private_key: object,
        certificate: object,
    ):
        self._xml_signer = xml_signer
        self._sunat_gateway = sunat_gateway
        self._repo = repo
        self._ubl_builder = ubl_builder
        self._zip_service = zip_service
        self._private_key = private_key
        self._certificate = certificate

    async def emitir_boleta(self, dto: EmitirBoletaRequest) -> EmitirBoletaResponse:
        ruc = Ruc(dto.ruc_emisor)
        serie_corr = SerieCorrelativo(dto.serie, dto.correlativo)
        moneda = Moneda.from_str(dto.moneda)
        items = self._map_items(dto.items)

        boleta = Boleta(
            ruc_emisor=ruc,
            serie_correlativo=serie_corr,
            moneda=moneda,
            items=items,
            fecha_emision=datetime.now(),
            tipo_doc_cliente=dto.tipo_doc_cliente,
            num_doc_cliente=dto.num_doc_cliente,
            nombre_cliente=dto.nombre_cliente,
        )

        ComprobanteDomainService.validar_montos(boleta)

        totales = ComprobanteDomainService.calcular_totales(items)
        xml_sin_firmar = self._ubl_builder.build_boleta(
            boleta, totales["subtotal"], totales["igv"], totales["total"]
        )
        xml_firmado = self._xml_signer.sign(
            xml_sin_firmar, self._private_key, self._certificate
        )
        xml_firmado_b64 = base64.b64encode(xml_firmado.encode("utf-8")).decode("utf-8")
        hash_cpe = hashlib.sha256(xml_firmado.encode("utf-8")).hexdigest().upper()

        filename = f"{dto.ruc_emisor}-{boleta.tipo.value}-{dto.serie}-{dto.correlativo:08d}"
        zip_bytes, _ = self._zip_service.compress(xml_firmado, filename)

        cdr = await self._sunat_gateway.send_bill(zip_bytes, f"{filename}.zip")

        cdr_xml_b64 = None
        if cdr.cdr_bytes:
            cdr_xml_b64 = base64.b64encode(cdr.cdr_bytes).decode("utf-8")

        boleta.marcar_emitido(
            xml_firmado_b64=xml_firmado_b64,
            hash_cpe=hash_cpe,
            cdr_xml_b64=cdr_xml_b64,
            cdr_codigo=cdr.codigo_respuesta,
            cdr_descripcion=cdr.descripcion,
            cdr_observaciones=cdr.observaciones,
        )

        await self._repo.save(boleta)

        return EmitirBoletaResponse(
            id=boleta.id,
            xml_firmado_b64=xml_firmado_b64,
            hash_cpe=hash_cpe,
            cdr_codigo=cdr.codigo_respuesta,
            cdr_descripcion=cdr.descripcion,
            cdr_observaciones=cdr.observaciones,
            estado=boleta.estado.value,
        )

    async def emitir_factura(self, dto: object) -> object:
        raise NotImplementedError("Usar EmitirFacturaUseCase")

    async def consultar(self, id: str) -> object:
        raise NotImplementedError("Usar ConsultarComprobanteUseCase")

    async def anular(self, id: str, motivo: str) -> object:
        raise NotImplementedError("Usar AnularComprobanteUseCase")

    @staticmethod
    def _map_items(items_dto: List[ItemDTO]) -> List[Item]:
        return [
            Item(
                descripcion=i.descripcion,
                cantidad=Decimal(str(i.cantidad)),
                precio_unitario=Decimal(str(i.precio_unitario)),
                igv_porcentaje=Decimal(str(i.igv_porcentaje)),
                unidad_medida=i.unidad_medida,
            )
            for i in items_dto
        ]
