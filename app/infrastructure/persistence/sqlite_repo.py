from __future__ import annotations
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.boleta import Boleta
from app.domain.entities.comprobante import (
    Comprobante,
    EstadoComprobante,
    Item,
    TipoComprobante,
)
from app.domain.entities.factura import Factura
from app.domain.ports.outbound.comprobante_repo import ComprobanteRepository
from app.domain.value_objects.moneda import Moneda
from app.domain.value_objects.ruc import Ruc
from app.domain.value_objects.serie_correlativo import SerieCorrelativo
from app.infrastructure.persistence.models import ComprobanteModel


class SqliteRepository(ComprobanteRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, comprobante: Comprobante) -> Comprobante:
        model = self._to_model(comprobante)
        self._session.add(model)
        await self._session.commit()
        await self._session.refresh(model)
        return comprobante

    async def find_by_id(self, id: str) -> Optional[Comprobante]:
        stmt = select(ComprobanteModel).where(ComprobanteModel.id == id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def find_by_serie_correlativo(
        self, ruc_emisor: str, serie: str, correlativo: int, tipo: str
    ) -> Optional[Comprobante]:
        stmt = select(ComprobanteModel).where(
            ComprobanteModel.ruc_emisor == ruc_emisor,
            ComprobanteModel.serie == serie,
            ComprobanteModel.correlativo == correlativo,
            ComprobanteModel.tipo == tipo,
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        if model is None:
            return None
        return self._to_entity(model)

    async def update(self, comprobante: Comprobante) -> Comprobante:
        model = await self._session.get(ComprobanteModel, comprobante.id)
        if model is None:
            raise ValueError(f"Comprobante {comprobante.id} no encontrado en BD")

        model.estado = comprobante.estado.value
        model.items = json.dumps(self._items_to_dict(comprobante.items), default=str)
        model.xml_firmado_b64 = comprobante.xml_firmado_b64
        model.hash_cpe = comprobante.hash_cpe
        model.cdr_xml_b64 = comprobante.cdr_xml_b64
        model.cdr_codigo = comprobante.cdr_codigo
        model.cdr_descripcion = comprobante.cdr_descripcion
        model.cdr_observaciones = comprobante.cdr_observaciones
        model.motivo_anulacion = comprobante.motivo_anulacion
        model.updated_at = datetime.now()

        await self._session.commit()
        return comprobante

    async def delete(self, id: str) -> None:
        stmt = sa_delete(ComprobanteModel).where(ComprobanteModel.id == id)
        await self._session.execute(stmt)
        await self._session.commit()

    @staticmethod
    def _to_model(c: Comprobante) -> ComprobanteModel:
        extra: Dict = {}
        if isinstance(c, Factura):
            extra["ruc_receptor"] = str(c.ruc_receptor) if c.ruc_receptor else None
            extra["razon_social_receptor"] = c.razon_social_receptor
        if isinstance(c, (Boleta, Factura)):
            extra["tipo_doc_cliente"] = getattr(c, "tipo_doc_cliente", None)
            extra["num_doc_cliente"] = getattr(c, "num_doc_cliente", None)
            extra["nombre_cliente"] = getattr(c, "nombre_cliente", None)

        return ComprobanteModel(
            id=c.id,
            ruc_emisor=str(c.ruc_emisor),
            serie=c.serie_correlativo.serie,
            correlativo=c.serie_correlativo.correlativo,
            tipo=c.tipo.value,
            fecha_emision=c.fecha_emision,
            moneda=c.moneda.value,
            estado=c.estado.value,
            items=json.dumps(SqliteRepository._items_to_dict(c.items), default=str),
            xml_firmado_b64=c.xml_firmado_b64,
            hash_cpe=c.hash_cpe,
            cdr_xml_b64=c.cdr_xml_b64,
            cdr_codigo=c.cdr_codigo,
            cdr_descripcion=c.cdr_descripcion,
            cdr_observaciones=c.cdr_observaciones,
            motivo_anulacion=c.motivo_anulacion,
            **extra,
        )

    @staticmethod
    def _to_entity(m: ComprobanteModel) -> Comprobante:
        items = SqliteRepository._items_from_dict(json.loads(m.items))
        ruc = Ruc(m.ruc_emisor)
        serie_corr = SerieCorrelativo(m.serie, m.correlativo)
        moneda = Moneda.from_str(m.moneda)
        estado = EstadoComprobante(m.estado)
        tipo = TipoComprobante(m.tipo)

        common = dict(
            id=m.id,
            ruc_emisor=ruc,
            serie_correlativo=serie_corr,
            moneda=moneda,
            items=items,
            fecha_emision=m.fecha_emision,
            estado=estado,
            xml_firmado_b64=m.xml_firmado_b64,
            hash_cpe=m.hash_cpe,
            cdr_xml_b64=m.cdr_xml_b64,
            cdr_codigo=m.cdr_codigo,
            cdr_descripcion=m.cdr_descripcion,
            cdr_observaciones=m.cdr_observaciones,
            motivo_anulacion=m.motivo_anulacion,
        )

        if tipo == TipoComprobante.FACTURA:
            ruc_rec = Ruc(m.ruc_receptor) if m.ruc_receptor else None
            return Factura(
                ruc_receptor=ruc_rec,
                razon_social_receptor=m.razon_social_receptor,
                tipo_doc_cliente=m.tipo_doc_cliente,
                num_doc_cliente=m.num_doc_cliente,
                nombre_cliente=m.nombre_cliente,
                **common,
            )

        return Boleta(
            tipo_doc_cliente=m.tipo_doc_cliente,
            num_doc_cliente=m.num_doc_cliente,
            nombre_cliente=m.nombre_cliente,
            **common,
        )

    @staticmethod
    def _items_to_dict(items: List[Item]) -> List[Dict]:
        return [
            {
                "descripcion": i.descripcion,
                "cantidad": str(i.cantidad),
                "precio_unitario": str(i.precio_unitario),
                "igv_porcentaje": str(i.igv_porcentaje),
                "unidad_medida": i.unidad_medida,
            }
            for i in items
        ]

    @staticmethod
    def _items_from_dict(data: List[Dict]) -> List[Item]:
        return [
            Item(
                descripcion=i["descripcion"],
                cantidad=Decimal(i["cantidad"]),
                precio_unitario=Decimal(i["precio_unitario"]),
                igv_porcentaje=Decimal(i.get("igv_porcentaje", "0.18")),
                unidad_medida=i.get("unidad_medida", "NIU"),
            )
            for i in data
        ]
