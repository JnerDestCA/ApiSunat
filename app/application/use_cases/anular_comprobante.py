from __future__ import annotations
import hashlib
import base64

from app.application.dtos.response_dto import AnulacionResponse
from app.domain.ports.inbound.comprobante_service import ComprobanteService
from app.domain.ports.outbound.comprobante_repo import ComprobanteRepository
from app.domain.ports.outbound.sunat_gateway import SunatGateway
from app.domain.ports.outbound.xml_signer import XmlSigner
from app.infrastructure.xml.ubl21_builder import Ubl21Builder
from app.infrastructure.zip.zip_service import ZipService
from datetime import date

class AnularComprobanteUseCase(ComprobanteService):
    def __init__(
        self,
        repo: ComprobanteRepository,
        xml_signer: XmlSigner,
        sunat_gateway: SunatGateway,
        ubl_builder: Ubl21Builder,
        zip_service: ZipService,
        private_key: object,
        certificate: object,
    ):
        self._repo = repo
        self._xml_signer = xml_signer
        self._sunat_gateway = sunat_gateway
        self._ubl_builder = ubl_builder
        self._zip_service = zip_service
        self._private_key = private_key
        self._certificate = certificate

    async def anular(self, id: str, motivo: str) -> AnulacionResponse:
        comprobante = await self._repo.find_by_id(id)
        if comprobante is None:
            raise ValueError(f"Comprobante {id} no encontrado")

        comprobante.anular(motivo)

        xml_sin_firmar = self._ubl_builder.build_anulacion(comprobante, motivo)
        xml_firmado = self._xml_signer.sign(
            xml_sin_firmar, self._private_key, self._certificate
        )

        # 👈 nombre correcto para comunicación de baja
        ruc = str(comprobante.ruc_emisor)
        hoy = date.today().strftime("%Y%m%d")
        filename = f"{ruc}-RA-{hoy}-1"

        zip_bytes, _ = self._zip_service.compress(xml_firmado, filename)

        # 👈 send_summary no send_bill
        cdr = await self._sunat_gateway.send_summary(zip_bytes, f"{filename}.zip")

        cdr_xml_b64 = None
        if cdr.cdr_bytes:
            cdr_xml_b64 = base64.b64encode(cdr.cdr_bytes).decode("utf-8")

        comprobante.cdr_xml_b64 = cdr_xml_b64
        comprobante.cdr_codigo = cdr.codigo_respuesta
        comprobante.cdr_descripcion = cdr.descripcion
        comprobante.cdr_observaciones = cdr.observaciones

        await self._repo.update(comprobante)

        return AnulacionResponse(
            id=comprobante.id,
            estado=comprobante.estado.value,
            cdr_codigo=cdr.codigo_respuesta,
            cdr_descripcion=cdr.descripcion,
            cdr_observaciones=cdr.observaciones,
            motivo=motivo,
        )

    async def emitir_boleta(self, dto: object) -> object:
        raise NotImplementedError

    async def emitir_factura(self, dto: object) -> object:
        raise NotImplementedError

    async def consultar(self, id: str) -> object:
        raise NotImplementedError
