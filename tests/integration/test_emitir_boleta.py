from __future__ import annotations
import os
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ["SUNAT_ENV"] = "beta"
os.environ["SUNAT_RUC"] = "20123456786"
os.environ["SUNAT_USUARIO_SOL"] = "TEST_USER"
os.environ["SUNAT_CLAVE_SOL"] = "TEST_PASS"
os.environ["PFX_PATH"] = "./tests/test_cert.pfx"
os.environ["PFX_PASSWORD"] = "test123"
os.environ["API_SECRET_KEY"] = "test_secret"

from app.domain.ports.outbound.sunat_gateway import CdrResponse, SunatGateway
from app.domain.ports.outbound.xml_signer import XmlSigner


def _payload_boleta(serie="B001", correlativo=1, ruc="20123456786"):
    return {
        "ruc_emisor": ruc,
        "serie": serie,
        "correlativo": correlativo,
        "moneda": "PEN",
        "items": [
            {
                "descripcion": "Producto Test",
                "cantidad": 1,
                "precio_unitario": "100.00",
            }
        ],
        "tipo_doc_cliente": "1",
        "num_doc_cliente": "12345678",
        "nombre_cliente": "Cliente Test",
    }


@pytest_asyncio.fixture
async def async_client():
    import importlib
    import app.config
    import app.infrastructure.persistence.database as db_mod

    db_file = f"./test_int_{uuid.uuid4().hex[:12]}.db"
    app.config.settings.database_url = f"sqlite+aiosqlite:///{db_file}"

    importlib.reload(db_mod)
    from app.infrastructure.persistence.database import init_db, async_session_factory

    from app.main import app

    await init_db()

    mock_sunat = MagicMock(spec=SunatGateway)
    mock_sunat.send_bill = AsyncMock(
        return_value=CdrResponse(
            codigo_respuesta="0",
            descripcion="Aceptado",
            cdr_bytes=b"<cdr>ok</cdr>",
            observaciones=None,
        )
    )
    mock_sunat.get_status = AsyncMock(
        return_value=CdrResponse(
            codigo_respuesta="0", descripcion="Ok", cdr_bytes=b"<cdr>ok</cdr>"
        )
    )

    mock_signer = MagicMock(spec=XmlSigner)
    mock_signer.sign = MagicMock(
        return_value='<?xml version="1.0" encoding="UTF-8"?><Invoice><signed>true</signed></Invoice>'
    )

    from app.infrastructure.xml.ubl21_builder import Ubl21Builder
    from app.infrastructure.zip.zip_service import ZipService
    from app.infrastructure.persistence.sqlite_repo import SqliteRepository
    from app.application.use_cases.emitir_boleta import EmitirBoletaUseCase
    from app.application.use_cases.consultar_comprobante import ConsultarComprobanteUseCase
    from app.application.use_cases.anular_comprobante import AnularComprobanteUseCase
    from app.application.use_cases.emitir_factura import EmitirFacturaUseCase

    async def _make_repo():
        async with async_session_factory() as session:
            return SqliteRepository(session)

    async def override_emitir_boleta_uc():
        repo = await _make_repo()
        return EmitirBoletaUseCase(
            xml_signer=mock_signer,
            sunat_gateway=mock_sunat,
            repo=repo,
            ubl_builder=Ubl21Builder(ruc_emisor="20123456786"),
            zip_service=ZipService(),
            private_key=MagicMock(),
            certificate=MagicMock(),
        )

    async def override_consultar_uc():
        repo = await _make_repo()
        return ConsultarComprobanteUseCase(repo=repo)

    async def override_anular_uc():
        repo = await _make_repo()
        return AnularComprobanteUseCase(
            repo=repo,
            xml_signer=mock_signer,
            sunat_gateway=mock_sunat,
            ubl_builder=Ubl21Builder(ruc_emisor="20123456786"),
            zip_service=ZipService(),
            private_key=MagicMock(),
            certificate=MagicMock(),
        )

    async def override_factura_uc():
        repo = await _make_repo()
        return EmitirFacturaUseCase(
            xml_signer=mock_signer,
            sunat_gateway=mock_sunat,
            repo=repo,
            ubl_builder=Ubl21Builder(ruc_emisor="20123456786"),
            zip_service=ZipService(),
            private_key=MagicMock(),
            certificate=MagicMock(),
        )

    from app.api.dependencies import (
        get_emitir_boleta_use_case,
        get_consultar_use_case,
        get_anular_use_case,
        get_emitir_factura_use_case,
    )

    app.dependency_overrides[get_emitir_boleta_use_case] = override_emitir_boleta_uc
    app.dependency_overrides[get_consultar_use_case] = override_consultar_uc
    app.dependency_overrides[get_anular_use_case] = override_anular_uc
    app.dependency_overrides[get_emitir_factura_use_case] = override_factura_uc

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()
    await db_mod.engine.dispose()

    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except PermissionError:
            pass


@pytest.mark.asyncio
async def test_emitir_boleta_flujo_completo(async_client):
    response = await async_client.post("/api/v1/boletas", json=_payload_boleta())
    assert response.status_code == 201
    data = response.json()
    assert data["estado"] == "EMITIDO"
    assert data["id"] is not None


@pytest.mark.asyncio
async def test_emitir_boleta_ruc_invalido(async_client):
    response = await async_client.post(
        "/api/v1/boletas", json=_payload_boleta(ruc="12345678901")
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_emitir_boleta_serie_invalida(async_client):
    response = await async_client.post(
        "/api/v1/boletas", json=_payload_boleta(serie="X001")
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    response = await async_client.get("/api/v1/comprobantes/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["sunat_env"] == "beta"


@pytest.mark.asyncio
async def test_consultar_comprobante_no_existe(async_client):
    response = await async_client.get("/api/v1/comprobantes/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_emitir_boleta_y_consultar(async_client):
    create_resp = await async_client.post(
        "/api/v1/boletas", json=_payload_boleta(correlativo=5)
    )
    assert create_resp.status_code == 201
    boleta_id = create_resp.json()["id"]

    get_resp = await async_client.get(f"/api/v1/comprobantes/{boleta_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == boleta_id
    assert data["serie"] == "B001"
    assert data["correlativo"] == 5
    assert data["estado"] == "EMITIDO"
    assert len(data["items"]) == 1
