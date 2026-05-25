from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Integer,
    DateTime,
    Text,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ComprobanteModel(Base):
    __tablename__ = "comprobantes"

    id = Column(String(36), primary_key=True)
    ruc_emisor = Column(String(11), nullable=False)
    serie = Column(String(4), nullable=False)
    correlativo = Column(Integer, nullable=False)
    tipo = Column(String(2), nullable=False)
    fecha_emision = Column(DateTime, nullable=False)
    moneda = Column(String(3), nullable=False)
    estado = Column(String(20), nullable=False)
    items = Column(Text, nullable=False)

    tipo_doc_cliente = Column(String(2), nullable=True)
    num_doc_cliente = Column(String(20), nullable=True)
    nombre_cliente = Column(String(200), nullable=True)

    ruc_receptor = Column(String(11), nullable=True)
    razon_social_receptor = Column(String(200), nullable=True)

    xml_firmado_b64 = Column(Text, nullable=True)
    hash_cpe = Column(String(64), nullable=True)

    cdr_xml_b64 = Column(Text, nullable=True)
    cdr_codigo = Column(String(10), nullable=True)
    cdr_descripcion = Column(Text, nullable=True)
    cdr_observaciones = Column(Text, nullable=True)

    motivo_anulacion = Column(String(100), nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "ruc_emisor", "serie", "correlativo", "tipo",
            name="uq_comprobante_serie_correlativo"
        ),
        Index("idx_comprobante_estado", "estado"),
        Index("idx_comprobante_fecha", "fecha_emision"),
    )
