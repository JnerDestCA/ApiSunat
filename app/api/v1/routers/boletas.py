from fastapi import APIRouter, Depends, status

from app.api.dependencies import get_emitir_boleta_use_case
from app.api.v1.schemas.boleta_schema import BoletaResponse, BoletaSchema
from app.application.dtos.boleta_dto import EmitirBoletaRequest, ItemDTO
from app.application.use_cases.emitir_boleta import EmitirBoletaUseCase

router = APIRouter(prefix="/api/v1/boletas", tags=["Boletas"])


@router.post("", response_model=BoletaResponse, status_code=status.HTTP_201_CREATED)
async def emitir_boleta(
    body: BoletaSchema,
    use_case: EmitirBoletaUseCase = Depends(get_emitir_boleta_use_case),
):
    dto = EmitirBoletaRequest(
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
        tipo_doc_cliente=body.tipo_doc_cliente,
        num_doc_cliente=body.num_doc_cliente,
        nombre_cliente=body.nombre_cliente,
    )
    result = await use_case.emitir_boleta(dto)
    return BoletaResponse(
        id=result.id,
        xml_firmado_b64=result.xml_firmado_b64,
        hash_cpe=result.hash_cpe,
        cdr_codigo=result.cdr_codigo,
        cdr_descripcion=result.cdr_descripcion,
        cdr_observaciones=result.cdr_observaciones,
        estado=result.estado,
    )
