from __future__ import annotations
import base64
from typing import Optional

import zeep
from zeep import helpers
from zeep.transports import Transport

from app.config import settings
from app.domain.ports.outbound.sunat_gateway import CdrResponse, SunatGateway
from app.infrastructure.sunat.sunat_endpoints import SUNAT_BETA_URL, SUNAT_PROD_URL


class SunatSoapAdapter(SunatGateway):
    def __init__(self):
        wsdl = SUNAT_PROD_URL if settings.is_produccion else SUNAT_BETA_URL
        self._client = zeep.Client(wsdl=wsdl, transport=Transport(timeout=60))
        self._username = settings.sunat_usuario_sol
        self._password = settings.sunat_clave_sol

    async def send_bill(self, zip_bytes: bytes, filename: str) -> CdrResponse:
        zip_b64 = base64.b64encode(zip_bytes).decode("utf-8")
        try:
            response = self._client.service.sendBill(
                fileName=filename,
                contentFile=zip_b64,
                _soapheaders={
                    "usuario": self._username,
                    "clave": self._password,
                },
            )
            return self._parse_response(response)
        except zeep.exceptions.Fault as e:
            return CdrResponse(
                codigo_respuesta="FAULT",
                descripcion=str(e),
                cdr_bytes=None,
            )

    async def get_status(self, ticket: str) -> CdrResponse:
        try:
            response = self._client.service.getStatus(
                ticket=ticket,
                _soapheaders={
                    "usuario": self._username,
                    "clave": self._password,
                },
            )
            return self._parse_response(response)
        except zeep.exceptions.Fault as e:
            return CdrResponse(
                codigo_respuesta="FAULT",
                descripcion=str(e),
                cdr_bytes=None,
            )

    async def send_summary(self, zip_bytes: bytes, filename: str) -> CdrResponse:
        zip_b64 = base64.b64encode(zip_bytes).decode("utf-8")
        try:
            response = self._client.service.sendSummary(
                fileName=filename,
                contentFile=zip_b64,
                _soapheaders={
                    "usuario": self._username,
                    "clave": self._password,
                },
            )
            return self._parse_response(response)
        except zeep.exceptions.Fault as e:
            return CdrResponse(
                codigo_respuesta="FAULT",
                descripcion=str(e),
                cdr_bytes=None,
            )

    def _parse_response(self, response: object) -> CdrResponse:
        if response is None:
            return CdrResponse(
                codigo_respuesta="ERROR",
                descripcion="Respuesta vacía de SUNAT",
                cdr_bytes=None,
            )
        resp_dict = helpers.serialize_object(response, dict)
        codigo = resp_dict.get("codigoRespuesta", "") or resp_dict.get(
            "codigo", ""
        )
        descripcion = resp_dict.get("descripcion", "")
        cdr_b64 = resp_dict.get("archivo", "") or resp_dict.get("cdr", "")
        observaciones = resp_dict.get("observaciones", None)

        cdr_bytes = None
        if cdr_b64:
            try:
                cdr_bytes = base64.b64decode(cdr_b64)
            except Exception:
                pass

        return CdrResponse(
            codigo_respuesta=str(codigo) if codigo else "0",
            descripcion=str(descripcion),
            cdr_bytes=cdr_bytes,
            observaciones=str(observaciones) if observaciones else None,
        )
