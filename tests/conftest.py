from __future__ import annotations
import os
from unittest.mock import AsyncMock, MagicMock

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID
from datetime import datetime, timedelta

os.environ["SUNAT_ENV"] = "beta"
os.environ["SUNAT_RUC"] = "20123456786"
os.environ["SUNAT_USUARIO_SOL"] = "TEST_USER"
os.environ["SUNAT_CLAVE_SOL"] = "TEST_PASS"
os.environ["PFX_PATH"] = "./tests/test_cert.pfx"
os.environ["PFX_PASSWORD"] = "test123"
os.environ["API_SECRET_KEY"] = "test_secret"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_sunat.db"

from app.domain.entities.boleta import Boleta
from app.domain.entities.comprobante import Item
from app.domain.entities.factura import Factura
from app.domain.ports.outbound.comprobante_repo import ComprobanteRepository
from app.domain.ports.outbound.sunat_gateway import CdrResponse, SunatGateway
from app.domain.ports.outbound.xml_signer import XmlSigner
from app.domain.value_objects.moneda import Moneda
from app.domain.value_objects.ruc import Ruc
from app.domain.value_objects.serie_correlativo import SerieCorrelativo


@pytest.fixture
def mock_sunat_gateway() -> SunatGateway:
    gateway = MagicMock(spec=SunatGateway)
    gateway.send_bill = AsyncMock(
        return_value=CdrResponse(
            codigo_respuesta="0",
            descripcion="La Factura numero F001-00000001 ha sido aceptada",
            cdr_bytes=b"<cdr>fake</cdr>",
            observaciones=None,
        )
    )
    gateway.get_status = AsyncMock(
        return_value=CdrResponse(
            codigo_respuesta="0",
            descripcion="Success",
            cdr_bytes=b"<cdr>fake</cdr>",
        )
    )
    return gateway


@pytest.fixture
def mock_xml_signer() -> XmlSigner:
    signer = MagicMock(spec=XmlSigner)
    signer.sign = MagicMock(
        return_value=(
            '<?xml version="1.0" encoding="UTF-8"?>'
            "<Invoice>"
            "<signed>true</signed>"
            "</Invoice>"
        )
    )
    return signer


@pytest.fixture
def mock_repo() -> ComprobanteRepository:
    repo = MagicMock(spec=ComprobanteRepository)
    repo.save = AsyncMock(side_effect=lambda c: c)
    repo.find_by_id = AsyncMock(return_value=None)
    repo.update = AsyncMock(side_effect=lambda c: c)
    repo.delete = AsyncMock()
    return repo


@pytest.fixture
def ruc_valido() -> Ruc:
    return Ruc("20123456786")


@pytest.fixture
def serie_boleta() -> SerieCorrelativo:
    return SerieCorrelativo("B001", 1)


@pytest.fixture
def serie_factura() -> SerieCorrelativo:
    return SerieCorrelativo("F001", 1)


@pytest.fixture
def item_valido() -> Item:
    return Item(
        descripcion="Producto de prueba",
        cantidad=2,
        precio_unitario=100,
    )


@pytest.fixture
def boleta_valida(ruc_valido, serie_boleta, item_valido) -> Boleta:
    return Boleta(
        ruc_emisor=ruc_valido,
        serie_correlativo=serie_boleta,
        moneda=Moneda.PEN,
        items=[item_valido],
        tipo_doc_cliente="1",
        num_doc_cliente="12345678",
        nombre_cliente="Cliente Prueba",
    )


@pytest.fixture
def factura_valida(ruc_valido, serie_factura, item_valido) -> Factura:
    return Factura(
        ruc_emisor=ruc_valido,
        serie_correlativo=serie_factura,
        moneda=Moneda.PEN,
        items=[item_valido],
        ruc_receptor=Ruc("20123456786"),
        razon_social_receptor="Receptor S.A.C.",
    )


def _generate_self_signed_key_and_cert():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [x509.NameAttribute(NameOID.COMMON_NAME, "Test SUNAT")]
    )
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(1000)
        .not_valid_before(datetime.now())
        .not_valid_after(datetime.now() + timedelta(days=365))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )
    return key, cert


@pytest.fixture(scope="session")
def test_key_and_cert():
    return _generate_self_signed_key_and_cert()
