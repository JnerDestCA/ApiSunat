from __future__ import annotations
import base64
from typing import Optional

import os
import requests
from requests import Session
from requests.auth import HTTPBasicAuth
import zeep
from zeep import helpers
from zeep.transports import Transport
from zeep.wsse.username import UsernameToken

from app.config import settings
from app.domain.ports.outbound.sunat_gateway import CdrResponse, SunatGateway
from app.infrastructure.sunat.sunat_endpoints import SUNAT_BETA_URL, SUNAT_PROD_URL


class SunatSoapAdapter(SunatGateway):
    def __init__(self):
        self._wsdl = SUNAT_PROD_URL if settings.is_produccion else SUNAT_BETA_URL
        self._username = settings.sunat_usuario_sol
        self._password = settings.sunat_clave_sol
        self._client = None

    def _get_client(self) -> zeep.Client:
        if self._client is None:
            wsdl_local = os.path.join(
                os.path.dirname(__file__), "wsdl", "billService.wsdl"
            )
            session = Session()
            session.auth = HTTPBasicAuth(self._username, self._password)
            
            self._client = zeep.Client(
                wsdl=wsdl_local,
                transport=Transport(session=session, timeout=60),
                wsse=UsernameToken(
                    username=self._username,
                    password=self._password,
                )
            )
        return self._client

    def _do_request(self, method: str, **kwargs) -> CdrResponse:
        try:
            service = self._get_client().service
            response = getattr(service, method)(**kwargs)
            return self._parse_response(response)
        except zeep.exceptions.Fault as e:
            print(f"SOAP FAULT: {e.message}")
            print(f"SOAP FAULT CODE: {e.code}")
            return CdrResponse(
                codigo_respuesta="FAULT",
                descripcion=str(e),
                cdr_bytes=None,
            )
        except requests.exceptions.RequestException as e:
            print(f"HTTP ERROR: {str(e)}")
            return CdrResponse(
                codigo_respuesta="FAULT",
                descripcion=str(e),
                cdr_bytes=None,
            )

    async def send_bill(self, zip_bytes: bytes, filename: str) -> CdrResponse:
        zip_b64 = base64.b64encode(zip_bytes).decode("utf-8")
        return self._do_request(   # 👈 ya sin _soapheaders
            "sendBill",
            fileName=filename,
            contentFile=zip_b64,
        )

    async def get_status(self, ticket: str) -> CdrResponse:
        return self._do_request(   # 👈 ya sin _soapheaders
            "getStatus",
            ticket=ticket,
        )

    async def send_summary(self, zip_bytes: bytes, filename: str) -> CdrResponse:
        zip_b64 = base64.b64encode(zip_bytes).decode("utf-8")
        return self._do_request(   # 👈 ya sin _soapheaders
            "sendSummary",
            fileName=filename,
            contentFile=zip_b64,
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
