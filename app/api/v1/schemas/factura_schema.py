from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from app.api.v1.schemas.boleta_schema import ItemSchema


class FacturaSchema(BaseModel):
    ruc_emisor: str = Field(..., min_length=11, max_length=11)
    serie: str = Field(..., min_length=4, max_length=4)
    correlativo: int = Field(..., ge=1, le=99999999)
    moneda: str = Field(default="PEN", pattern=r"^(PEN|USD|EUR)$")
    items: List[ItemSchema] = Field(..., min_length=1)
    ruc_receptor: str = Field(..., min_length=11, max_length=11)
    razon_social_receptor: str = Field(..., min_length=1, max_length=200)
    tipo_doc_cliente: Optional[str] = Field(default=None, pattern=r"^(1|6)$")
    num_doc_cliente: Optional[str] = Field(default=None, max_length=20)
    nombre_cliente: Optional[str] = Field(default=None, max_length=200)

    @field_validator("ruc_emisor")
    @classmethod
    def validar_ruc_emisor(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 11:
            raise ValueError("RUC emisor debe tener 11 dígitos numéricos")
        pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        suma = sum(int(v[i]) * pesos[i] for i in range(10))
        residuo = suma % 11
        digito = 11 - residuo
        if digito == 11:
            digito = 0
        elif digito == 10:
            digito = 0
        if digito != int(v[10]):
            raise ValueError(f"RUC emisor {v} tiene dígito verificador inválido")
        return v

    @field_validator("ruc_receptor")
    @classmethod
    def validar_ruc_receptor(cls, v: str) -> str:
        if not v.isdigit() or len(v) != 11:
            raise ValueError("RUC receptor debe tener 11 dígitos numéricos")
        pesos = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        suma = sum(int(v[i]) * pesos[i] for i in range(10))
        residuo = suma % 11
        digito = 11 - residuo
        if digito == 11:
            digito = 0
        elif digito == 10:
            digito = 0
        if digito != int(v[10]):
            raise ValueError(f"RUC receptor {v} tiene dígito verificador inválido")
        return v

    @field_validator("serie")
    @classmethod
    def validar_serie(cls, v: str) -> str:
        v = v.upper()
        if not v.startswith("F"):
            raise ValueError("Serie de factura debe comenzar con F (ej: F001)")
        if not v[1:].isdigit() or len(v) != 4:
            raise ValueError("Serie debe tener formato: F001")
        return v


class FacturaResponse(BaseModel):
    id: str
    xml_firmado_b64: Optional[str] = None
    hash_cpe: Optional[str] = None
    cdr_codigo: Optional[str] = None
    cdr_descripcion: Optional[str] = None
    cdr_observaciones: Optional[str] = None
    estado: str = "EMITIDO"
