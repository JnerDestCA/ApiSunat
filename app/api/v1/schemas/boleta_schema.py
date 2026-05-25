from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class ItemSchema(BaseModel):
    descripcion: str = Field(..., min_length=1, max_length=500)
    cantidad: Decimal = Field(..., gt=0)
    precio_unitario: Decimal = Field(..., ge=0)
    igv_porcentaje: Decimal = Field(default=Decimal("0.18"), ge=0, le=1)
    unidad_medida: str = Field(default="NIU", min_length=1, max_length=4)


class BoletaSchema(BaseModel):
    ruc_emisor: str = Field(..., min_length=11, max_length=11)
    serie: str = Field(..., min_length=4, max_length=4)
    correlativo: int = Field(..., ge=1, le=99999999)
    moneda: str = Field(default="PEN", pattern=r"^(PEN|USD|EUR)$")
    items: List[ItemSchema] = Field(..., min_length=1)
    tipo_doc_cliente: Optional[str] = Field(default=None, pattern=r"^(1|6)$")
    num_doc_cliente: Optional[str] = Field(default=None, max_length=20)
    nombre_cliente: Optional[str] = Field(default=None, max_length=200)

    @field_validator("ruc_emisor")
    @classmethod
    def validar_ruc(cls, v: str) -> str:
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
            raise ValueError(f"RUC {v} tiene dígito verificador inválido")
        return v

    @field_validator("serie")
    @classmethod
    def validar_serie(cls, v: str) -> str:
        v = v.upper()
        if not (v.startswith("B") or v.startswith("F")):
            raise ValueError("Serie debe comenzar con B (boleta) o F (factura)")
        if not v[1:].isdigit() or len(v) != 4:
            raise ValueError("Serie debe tener formato: B001 o F001")
        return v

    @field_validator("tipo_doc_cliente")
    @classmethod
    def validar_tipo_doc(cls, v: Optional[str], info) -> Optional[str]:
        num_doc = info.data.get("num_doc_cliente")
        if v and num_doc:
            if v == "6" and len(num_doc) != 11:
                raise ValueError("RUC de cliente debe tener 11 dígitos")
            if v == "1" and len(num_doc) not in (8, 12):
                raise ValueError("DNI debe tener 8 dígitos")
        return v


class BoletaResponse(BaseModel):
    id: str
    xml_firmado_b64: Optional[str] = None
    hash_cpe: Optional[str] = None
    cdr_codigo: Optional[str] = None
    cdr_descripcion: Optional[str] = None
    cdr_observaciones: Optional[str] = None
    estado: str = "EMITIDO"
