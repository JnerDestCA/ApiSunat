from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.routers import boletas, consultas, facturas
from app.infrastructure.persistence.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="API Facturación Electrónica SUNAT",
    description=(
        "API para emisión, consulta y anulación de comprobantes electrónicos "
        "(boletas y facturas) bajo el estándar UBL 2.1 de SUNAT Perú.\n\n"
        "## Autenticación\n"
        "La comunicación con SUNAT requiere credenciales SOL (usuario y clave) "
        "configuradas en las variables de entorno `SUNAT_USUARIO_SOL` y `SUNAT_CLAVE_SOL`.\n\n"
        "## Firma Digital\n"
        "Los XML son firmados digitalmente usando un certificado .pfx "
        "configurado en `PFX_PATH` y `PFX_PASSWORD`.\n\n"
        "## Entornos\n"
        "- **Beta**: `SUNAT_ENV=beta` (para pruebas)\n"
        "- **Producción**: `SUNAT_ENV=produccion`\n\n"
        "Consulta la documentación de cada endpoint para más detalles."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(boletas.router)
app.include_router(facturas.router)
app.include_router(consultas.router)
