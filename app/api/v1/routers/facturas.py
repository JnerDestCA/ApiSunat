from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_emitir_factura_use_case
from app.api.v1.schemas.factura_schema import FacturaResponse, FacturaSchema
from app.application.dtos.boleta_dto import ItemDTO
from app.application.dtos.factura_dto import EmitirFacturaRequest
from app.application.use_cases.emitir_factura import EmitirFacturaUseCase

router = APIRouter(prefix="/api/v1/facturas", tags=["Facturas"])


@router.post("", response_model=FacturaResponse, status_code=status.HTTP_201_CREATED)
async def emitir_factura(
    body: FacturaSchema,
    use_case: EmitirFacturaUseCase = Depends(get_emitir_factura_use_case),
):
    dto = EmitirFacturaRequest(
        ruc_emisor=body.ruc_emisor,
        serie=body.serie,
        correlativo=body.correlativo,
        moneda=body.moneda,
        items=[
            ItemDTO(
                descripcion=i.descripcion,
                cantidad=i.cantidad,
                precio_unitario=i.precio_unitario,
                igv_porcentaje=i.igv_porcentaje,
                unidad_medida=i.unidad_medida,
            )
            for i in body.items
        ],
        ruc_receptor=body.ruc_receptor,
        razon_social_receptor=body.razon_social_receptor,
        tipo_doc_cliente=body.tipo_doc_cliente,
        num_doc_cliente=body.num_doc_cliente,
        nombre_cliente=body.nombre_cliente,
    )
    result = await use_case.emitir_factura(dto)
    return FacturaResponse(
        id=result.id,
        xml_firmado_b64=result.xml_firmado_b64,
        hash_cpe=result.hash_cpe,
        cdr_codigo=result.cdr_codigo,
        cdr_descripcion=result.cdr_descripcion,
        cdr_observaciones=result.cdr_observaciones,
        estado=result.estado,
    )
