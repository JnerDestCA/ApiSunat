from __future__ import annotations
from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.use_cases.anular_comprobante import AnularComprobanteUseCase
from app.application.use_cases.consultar_comprobante import ConsultarComprobanteUseCase
from app.application.use_cases.emitir_boleta import EmitirBoletaUseCase
from app.application.use_cases.emitir_factura import EmitirFacturaUseCase
from app.config import settings
from app.infrastructure.certificate.pfx_loader import load_pfx
from app.infrastructure.persistence.database import get_session
from app.infrastructure.persistence.sqlite_repo import SqliteRepository
from app.infrastructure.sunat.sunat_soap_adapter import SunatSoapAdapter
from app.infrastructure.xml.ubl21_builder import Ubl21Builder
from app.infrastructure.xml.xml_signer_adapter import XmlSignerAdapter
from app.infrastructure.zip.zip_service import ZipService


@lru_cache(maxsize=1)
def _get_certificate():
    return load_pfx(settings.pfx_path, settings.pfx_password)


@lru_cache(maxsize=1)
def _get_xml_signer() -> XmlSignerAdapter:
    return XmlSignerAdapter()


@lru_cache(maxsize=1)
def _get_sunat_gateway() -> SunatSoapAdapter:
    return SunatSoapAdapter()


@lru_cache(maxsize=1)
def _get_ubl_builder() -> Ubl21Builder:
    return Ubl21Builder()


@lru_cache(maxsize=1)
def _get_zip_service() -> ZipService:
    return ZipService()


async def get_repo(session: AsyncSession = Depends(get_session)) -> SqliteRepository:
    return SqliteRepository(session)


async def get_emitir_boleta_use_case(
    repo: SqliteRepository = Depends(get_repo),
) -> EmitirBoletaUseCase:
    private_key, certificate = _get_certificate()
    return EmitirBoletaUseCase(
        xml_signer=_get_xml_signer(),
        sunat_gateway=_get_sunat_gateway(),
        repo=repo,
        ubl_builder=_get_ubl_builder(),
        zip_service=_get_zip_service(),
        private_key=private_key,
        certificate=certificate,
    )


async def get_emitir_factura_use_case(
    repo: SqliteRepository = Depends(get_repo),
) -> EmitirFacturaUseCase:
    private_key, certificate = _get_certificate()
    return EmitirFacturaUseCase(
        xml_signer=_get_xml_signer(),
        sunat_gateway=_get_sunat_gateway(),
        repo=repo,
        ubl_builder=_get_ubl_builder(),
        zip_service=_get_zip_service(),
        private_key=private_key,
        certificate=certificate,
    )


async def get_consultar_use_case(
    repo: SqliteRepository = Depends(get_repo),
) -> ConsultarComprobanteUseCase:
    return ConsultarComprobanteUseCase(repo=repo)


async def get_anular_use_case(
    repo: SqliteRepository = Depends(get_repo),
) -> AnularComprobanteUseCase:
    private_key, certificate = _get_certificate()
    return AnularComprobanteUseCase(
        repo=repo,
        xml_signer=_get_xml_signer(),
        sunat_gateway=_get_sunat_gateway(),
        ubl_builder=_get_ubl_builder(),
        zip_service=_get_zip_service(),
        private_key=private_key,
        certificate=certificate,
    )
