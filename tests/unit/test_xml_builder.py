from decimal import Decimal
from datetime import datetime

import pytest
from lxml import etree

from app.domain.entities.boleta import Boleta
from app.domain.entities.comprobante import Item
from app.domain.value_objects.moneda import Moneda
from app.domain.value_objects.ruc import Ruc
from app.domain.value_objects.serie_correlativo import SerieCorrelativo
from app.infrastructure.xml.ubl21_builder import (
    Ubl21Builder,
    NS_CBC,
    NS_CAC,
    NS_EXT,
    NS_DS,
)


@pytest.fixture
def builder():
    return Ubl21Builder(razon_social="MI EMPRESA S.A.C.")


@pytest.fixture
def boleta_ejemplo():
    ruc = Ruc("20123456786")
    serie = SerieCorrelativo("B001", 1)
    items = [
        Item(
            descripcion="Laptop Gamer",
            cantidad=1,
            precio_unitario=Decimal("2500.00"),
        ),
        Item(
            descripcion="Mouse USB",
            cantidad=2,
            precio_unitario=Decimal("50.00"),
        ),
    ]
    return Boleta(
        ruc_emisor=ruc,
        serie_correlativo=serie,
        moneda=Moneda.PEN,
        items=items,
        fecha_emision=datetime(2025, 6, 1, 10, 30, 0),
        tipo_doc_cliente="1",
        num_doc_cliente="12345678",
        nombre_cliente="Juan Perez",
    )


class TestXmlBuilder:
    def test_namespaces_ubl_presentes(self, builder, boleta_ejemplo):
        xml_str = builder.build_boleta(
            boleta_ejemplo, Decimal("2600.00"), Decimal("468.00"), Decimal("3068.00")
        )
        root = etree.fromstring(xml_str.encode("utf-8"))
        assert root.tag == f"{{{NS_CAC}}}Invoice"

    def test_ublextensions_presente(self, builder, boleta_ejemplo):
        xml_str = builder.build_boleta(
            boleta_ejemplo, Decimal("2600.00"), Decimal("468.00"), Decimal("3068.00")
        )
        root = etree.fromstring(xml_str.encode("utf-8"))
        ext = root.find(f"{{{NS_EXT}}}UBLExtensions")
        assert ext is not None

    def test_placeholder_firma_vacio(self, builder, boleta_ejemplo):
        xml_str = builder.build_boleta(
            boleta_ejemplo, Decimal("2600.00"), Decimal("468.00"), Decimal("3068.00")
        )
        root = etree.fromstring(xml_str.encode("utf-8"))
        ext_content = root.find(
            f".//{{{NS_EXT}}}ExtensionContent"
        )
        assert ext_content is not None

    def test_calculo_igv_correcto(self, builder, boleta_ejemplo):
        items = boleta_ejemplo.items
        subtotal = sum(i.subtotal for i in items)
        igv = sum(i.igv for i in items)
        total = sum(i.total for i in items)

        subtotal = subtotal.quantize(Decimal("0.01"))
        igv = igv.quantize(Decimal("0.01"))
        total = total.quantize(Decimal("0.01"))

        assert subtotal == Decimal("2600.00")
        assert igv == Decimal("468.00")
        assert total == Decimal("3068.00")

    def test_formato_fecha_iso(self, builder, boleta_ejemplo):
        xml_str = builder.build_boleta(
            boleta_ejemplo, Decimal("2600.00"), Decimal("468.00"), Decimal("3068.00")
        )
        root = etree.fromstring(xml_str.encode("utf-8"))
        issue_date = root.find(f"{{{NS_CBC}}}IssueDate")
        assert issue_date is not None
        assert issue_date.text == "2025-06-01"

    def test_codigo_tipo_boleta_03(self, builder, boleta_ejemplo):
        xml_str = builder.build_boleta(
            boleta_ejemplo, Decimal("2600.00"), Decimal("468.00"), Decimal("3068.00")
        )
        root = etree.fromstring(xml_str.encode("utf-8"))
        type_code = root.find(f"{{{NS_CBC}}}InvoiceTypeCode")
        assert type_code is not None
        assert type_code.text == "03"
        assert type_code.get("listID") == "0101"

    def test_moneda_en_documento(self, builder, boleta_ejemplo):
        xml_str = builder.build_boleta(
            boleta_ejemplo, Decimal("2600.00"), Decimal("468.00"), Decimal("3068.00")
        )
        root = etree.fromstring(xml_str.encode("utf-8"))
        currency = root.find(f"{{{NS_CBC}}}DocumentCurrencyCode")
        assert currency is not None
        assert currency.text == "PEN"

    def test_serie_correlativo_en_id(self, builder, boleta_ejemplo):
        xml_str = builder.build_boleta(
            boleta_ejemplo, Decimal("2600.00"), Decimal("468.00"), Decimal("3068.00")
        )
        root = etree.fromstring(xml_str.encode("utf-8"))
        doc_id = root.find(f"{{{NS_CBC}}}ID")
        assert doc_id is not None
        assert doc_id.text == "B001-00000001"

    def test_items_en_xml(self, builder, boleta_ejemplo):
        xml_str = builder.build_boleta(
            boleta_ejemplo, Decimal("2600.00"), Decimal("468.00"), Decimal("3068.00")
        )
        root = etree.fromstring(xml_str.encode("utf-8"))
        lines = root.findall(f"{{{NS_CAC}}}InvoiceLine")
        assert len(lines) == 2
        descs = [
            line.find(f"{{{NS_CAC}}}Item/{{{NS_CBC}}}Description")
            for line in lines
        ]
        assert descs[0].text == "Laptop Gamer"
        assert descs[1].text == "Mouse USB"

    def test_total_legal_monetary(self, builder, boleta_ejemplo):
        xml_str = builder.build_boleta(
            boleta_ejemplo, Decimal("2600.00"), Decimal("468.00"), Decimal("3068.00")
        )
        root = etree.fromstring(xml_str.encode("utf-8"))
        legal = root.find(f"{{{NS_CAC}}}LegalMonetaryTotal")
        payable = legal.find(f"{{{NS_CBC}}}PayableAmount")
        assert payable is not None
        assert payable.text == "3068.00"
