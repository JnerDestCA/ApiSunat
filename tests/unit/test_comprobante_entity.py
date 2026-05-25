from decimal import Decimal

import pytest

from app.domain.entities.boleta import Boleta
from app.domain.entities.comprobante import EstadoComprobante, Item
from app.domain.entities.factura import Factura
from app.domain.value_objects.moneda import Moneda
from app.domain.value_objects.ruc import Ruc
from app.domain.value_objects.serie_correlativo import SerieCorrelativo


@pytest.fixture
def ruc_valido():
    return Ruc("20123456786")


@pytest.fixture
def serie_boleta():
    return SerieCorrelativo("B001", 1)


@pytest.fixture
def serie_factura():
    return SerieCorrelativo("F001", 1)


class TestItem:
    def test_item_valido(self):
        item = Item(
            descripcion="Producto",
            cantidad=2,
            precio_unitario=Decimal("100.00"),
        )
        assert item.subtotal == Decimal("200.00")
        assert item.igv == Decimal("36.00")
        assert item.total == Decimal("236.00")

    def test_item_cantidad_cero_lanza_error(self):
        with pytest.raises(ValueError, match="positiva"):
            Item(
                descripcion="Producto",
                cantidad=0,
                precio_unitario=Decimal("100.00"),
            )

    def test_item_cantidad_negativa_lanza_error(self):
        with pytest.raises(ValueError, match="positiva"):
            Item(
                descripcion="Producto",
                cantidad=-1,
                precio_unitario=Decimal("100.00"),
            )

    def test_item_precio_negativo_lanza_error(self):
        with pytest.raises(ValueError, match="negativo"):
            Item(
                descripcion="Producto",
                cantidad=1,
                precio_unitario=Decimal("-10.00"),
            )

    def test_item_descripcion_vacia_lanza_error(self):
        with pytest.raises(ValueError, match="vacía"):
            Item(
                descripcion="   ",
                cantidad=1,
                precio_unitario=Decimal("100.00"),
            )

    def test_item_igv_porcentaje_personalizado(self):
        item = Item(
            descripcion="Exportación",
            cantidad=1,
            precio_unitario=Decimal("1000.00"),
            igv_porcentaje=Decimal("0.00"),
        )
        assert item.igv == Decimal("0.00")
        assert item.total == Decimal("1000.00")

    def test_item_unidad_medida_default(self):
        item = Item(
            descripcion="Producto",
            cantidad=1,
            precio_unitario=Decimal("100.00"),
        )
        assert item.unidad_medida == "NIU"


class TestBoleta:
    def test_boleta_valida(self, ruc_valido, serie_boleta):
        boleta = Boleta(
            ruc_emisor=ruc_valido,
            serie_correlativo=serie_boleta,
            moneda=Moneda.PEN,
            items=[
                Item(
                    descripcion="Producto",
                    cantidad=1,
                    precio_unitario=Decimal("100.00"),
                )
            ],
            tipo_doc_cliente="1",
            num_doc_cliente="12345678",
            nombre_cliente="Juan Perez",
        )
        assert boleta.tipo.value == "03"
        assert boleta.estado == EstadoComprobante.EMITIDO
        assert boleta.total == Decimal("118.00")

    def test_boleta_sin_items_lanza_error(self, ruc_valido, serie_boleta):
        with pytest.raises(ValueError, match="al menos un item"):
            Boleta(
                ruc_emisor=ruc_valido,
                serie_correlativo=serie_boleta,
                moneda=Moneda.PEN,
                items=[],
            )

    def test_boleta_anular(self, ruc_valido, serie_boleta):
        boleta = Boleta(
            ruc_emisor=ruc_valido,
            serie_correlativo=serie_boleta,
            moneda=Moneda.PEN,
            items=[
                Item(
                    descripcion="Producto",
                    cantidad=1,
                    precio_unitario=Decimal("100.00"),
                )
            ],
        )
        boleta.anular("Error en datos del cliente")
        assert boleta.estado == EstadoComprobante.ANULADO
        assert boleta.motivo_anulacion == "Error en datos del cliente"

    def test_boleta_anular_sin_motivo_lanza_error(self, ruc_valido, serie_boleta):
        boleta = Boleta(
            ruc_emisor=ruc_valido,
            serie_correlativo=serie_boleta,
            moneda=Moneda.PEN,
            items=[
                Item(
                    descripcion="Producto",
                    cantidad=1,
                    precio_unitario=Decimal("100.00"),
                )
            ],
        )
        with pytest.raises(ValueError, match="5 y 100"):
            boleta.anular("ab")

    def test_boleta_anular_dos_veces_lanza_error(self, ruc_valido, serie_boleta):
        boleta = Boleta(
            ruc_emisor=ruc_valido,
            serie_correlativo=serie_boleta,
            moneda=Moneda.PEN,
            items=[
                Item(
                    descripcion="Producto",
                    cantidad=1,
                    precio_unitario=Decimal("100.00"),
                )
            ],
        )
        boleta.anular("Error en el precio")
        with pytest.raises(ValueError, match="No se puede anular"):
            boleta.anular("Otro motivo")

    def test_boleta_marcar_emitido(self, ruc_valido, serie_boleta):
        boleta = Boleta(
            ruc_emisor=ruc_valido,
            serie_correlativo=serie_boleta,
            moneda=Moneda.PEN,
            items=[
                Item(
                    descripcion="Producto",
                    cantidad=1,
                    precio_unitario=Decimal("100.00"),
                )
            ],
        )
        boleta.marcar_emitido(
            xml_firmado_b64="ZmFrZQ==",
            hash_cpe="ABC123",
            cdr_xml_b64="Y2Ry",
            cdr_codigo="0",
            cdr_descripcion="Aceptado",
        )
        assert boleta.xml_firmado_b64 == "ZmFrZQ=="
        assert boleta.hash_cpe == "ABC123"
        assert boleta.cdr_codigo == "0"


class TestFactura:
    def test_factura_valida(self, ruc_valido, serie_factura):
        factura = Factura(
            ruc_emisor=ruc_valido,
            serie_correlativo=serie_factura,
            moneda=Moneda.PEN,
            items=[
                Item(
                    descripcion="Producto",
                    cantidad=1,
                    precio_unitario=Decimal("100.00"),
                )
            ],
            ruc_receptor=Ruc("20123456786"),
            razon_social_receptor="Receptor S.A.C.",
        )
        assert factura.tipo.value == "01"
        assert factura.total == Decimal("118.00")

    def test_factura_sin_ruc_receptor_lanza_error(self, ruc_valido, serie_factura):
        with pytest.raises(ValueError, match="ruc_receptor"):
            Factura(
                ruc_emisor=ruc_valido,
                serie_correlativo=serie_factura,
                moneda=Moneda.PEN,
                items=[
                    Item(
                        descripcion="Producto",
                        cantidad=1,
                        precio_unitario=Decimal("100.00"),
                    )
                ],
                ruc_receptor=None,
                razon_social_receptor="Receptor S.A.C.",
            )

    def test_factura_sin_razon_social_lanza_error(self, ruc_valido, serie_factura):
        with pytest.raises(ValueError, match="razon_social_receptor"):
            Factura(
                ruc_emisor=ruc_valido,
                serie_correlativo=serie_factura,
                moneda=Moneda.PEN,
                items=[
                    Item(
                        descripcion="Producto",
                        cantidad=1,
                        precio_unitario=Decimal("100.00"),
                    )
                ],
                ruc_receptor=Ruc("20123456786"),
                razon_social_receptor="",
            )


class TestSerieCorrelativo:
    def test_serie_boleta_valida(self):
        sc = SerieCorrelativo("B001", 1)
        assert sc.serie == "B001"
        assert sc.correlativo == 1
        assert sc.tipo == "03"

    def test_serie_factura_valida(self):
        sc = SerieCorrelativo("F001", 1)
        assert sc.serie == "F001"
        assert sc.correlativo == 1
        assert sc.tipo == "01"

    def test_serie_formato_invalido(self):
        with pytest.raises(ValueError, match="inválida"):
            SerieCorrelativo("X001", 1)

    def test_correlativo_cero_lanza_error(self):
        with pytest.raises(ValueError, match="inválido"):
            SerieCorrelativo("F001", 0)

    def test_str_representation(self):
        sc = SerieCorrelativo("F001", 1)
        assert str(sc) == "F001-00000001"


class TestMoneda:
    def test_moneda_pen(self):
        assert Moneda.from_str("PEN") == Moneda.PEN

    def test_moneda_usd(self):
        assert Moneda.from_str("usd") == Moneda.USD

    def test_moneda_invalida(self):
        with pytest.raises(ValueError, match="inválida"):
            Moneda.from_str("BTC")
