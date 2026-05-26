# Flujo de Boletas y Facturas — Documentación de Arquitectura

## Arquitectura General (Hexagonal / Clean Architecture)

```
┌─────────────────────────────────────────────────────┐
│                   API Layer                          │
│   FastAPI routers + Pydantic schemas + Dependencias  │
├─────────────────────────────────────────────────────┤
│               Application Layer                      │
│   Use Cases (EmitirBoleta, EmitirFactura, etc.)      │
│   DTOs (EmitirBoletaRequest/Response, etc.)          │
├─────────────────────────────────────────────────────┤
│                Domain Layer                          │
│   Entities (Comprobante, Boleta, Factura, Item)      │
│   Value Objects (Ruc, Moneda, SerieCorrelativo)      │
│   Domain Services (ComprobanteDomainService)         │
│   Ports (interfaces: inbound/outbound)               │
├─────────────────────────────────────────────────────┤
│              Infrastructure Layer                    │
│   XML: Ubl21Builder, XmlSignerAdapter                │
│   ZIP: ZipService                                    │
│   SOAP: SunatSoapAdapter                             │
│   Cert: pfx_loader                                   │
│   Persistencia: SqliteRepository, Models, Database   │
└─────────────────────────────────────────────────────┘
```

---

# Clases y Funciones por Capa

## 1. Capa de Dominio (`app/domain/`)

### 1.1 Value Objects (`app/domain/value_objects/`)

#### `Ruc` (`ruc.py`)
| Miembro | Tipo | Descripción |
|---------|------|-------------|
| `__init__(value)` | constructor | Limpia y valida RUC (11 dígitos + dígito verificador con pesos `[5,4,3,2,7,6,5,4,3,2]`) |
| `_validar_digito_verificador(ruc)` | estático | Algoritmo módulo 11 para el último dígito |
| `value` | property | Retorna el string del RUC |

#### `Moneda` (`moneda.py`)
| Miembro | Tipo | Descripción |
|---------|------|-------------|
| `PEN`, `USD`, `EUR` | enum | Códigos de moneda |
| `from_str(value)` | classmethod | Convierte string a enum, valida valor |

#### `SerieCorrelativo` (`serie_correlativo.py`)
| Miembro | Tipo | Descripción |
|---------|------|-------------|
| `__init__(serie, correlativo)` | constructor | Valida serie `F001`-`F999` o `B001`-`B999`; correlativo 1-99999999 |
| `serie` | property | String de la serie |
| `correlativo` | property | Entero del correlativo |
| `tipo` | property | `"01"` si serie empieza con F, `"03"` si empieza con B |
| `__str__` | | Formato `"F001-00000001"` |

---

### 1.2 Entidades (`app/domain/entities/`)

#### `Comprobante` (`comprobante.py`) — Clase base
| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `ruc_emisor` | `Ruc` | RUC del emisor |
| `serie_correlativo` | `SerieCorrelativo` | Serie y número correlativo |
| `tipo` | `TipoComprobante` | No se inicializa directo; lo asigna la subclase |
| `moneda` | `Moneda` | Moneda del comprobante |
| `items` | `List[Item]` | Lista de ítems |
| `id` | `str` | UUID v4 autogenerado |
| `fecha_emision` | `datetime` | Fecha de emisión |
| `estado` | `EstadoComprobante` | EMITIDO, ANULADO, RECHAZADO |
| `xml_firmado_b64` | `str?` | XML firmado en base64 |
| `hash_cpe` | `str?` | SHA-256 del XML firmado (hex mayúscula) |
| `cdr_xml_b64` | `str?` | CDR de SUNAT en base64 |
| `cdr_codigo` | `str?` | Código de respuesta SUNAT |
| `cdr_descripcion` | `str?` | Descripción de respuesta SUNAT |
| `cdr_observaciones` | `str?` | Observaciones del CDR |
| `motivo_anulacion` | `str?` | Motivo de anulación |

| Método | Descripción |
|--------|-------------|
| `total_igv` (property) | Suma del IGV de todos los items |
| `total_subtotal` (property) | Suma de subtotales de todos los items |
| `total` (property) | Suma del total (subtotal + igv) de todos los items |
| `anular(motivo)` | Cambia estado a ANULADO, valida motivo (5-100 chars) |
| `marcar_emitido(xml_firmado_b64, hash_cpe, cdr_xml_b64, cdr_codigo, cdr_descripcion, cdr_observaciones)` | Almacena datos post-emisión exitosa |

#### `Item` (`comprobante.py`)
| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `descripcion` | `str` | Descripción (no vacía) |
| `cantidad` | `Decimal` | Cantidad (> 0) |
| `precio_unitario` | `Decimal` | Precio unitario (>= 0) |
| `igv_porcentaje` | `Decimal` | 0.18 por defecto |
| `unidad_medida` | `str` | "NIU" por defecto |

| Método | Descripción |
|--------|-------------|
| `__post_init__` | Valida cantidad > 0, precio >= 0, descripción no vacía |
| `subtotal` (property) | `cantidad * precio_unitario`, redondeado a 2 decimales |
| `igv` (property) | `subtotal * igv_porcentaje`, redondeado a 2 decimales |
| `total` (property) | `subtotal + igv`, redondeado a 2 decimales |

#### `Boleta` (`boleta.py`) — extiende `Comprobante`
| Atributo adicional | Tipo | Descripción |
|-------------------|------|-------------|
| `tipo_doc_cliente` | `str?` | "1" (DNI) o "6" (RUC) |
| `num_doc_cliente` | `str?` | Número de documento del cliente |
| `nombre_cliente` | `str?` | Nombre o razón social del cliente |

- `tipo` se fija como `TipoComprobante.BOLETA` (`"03"`)

#### `Factura` (`factura.py`) — extiende `Comprobante`
| Atributo adicional | Tipo | Descripción |
|-------------------|------|-------------|
| `ruc_receptor` | `Ruc?` | RUC del receptor (obligatorio) |
| `razon_social_receptor` | `str?` | Razón social del receptor (obligatorio) |
| `tipo_doc_cliente` | `str?` | "1" (DNI) o "6" (RUC) |
| `num_doc_cliente` | `str?` | Número de documento del cliente |
| `nombre_cliente` | `str?` | Nombre o razón social del cliente |

- `tipo` se fija como `TipoComprobante.FACTURA` (`"01"`)
- Requiere `ruc_receptor` y `razon_social_receptor` no nulos

#### Enums (`comprobante.py`)
| Enum | Valores |
|------|---------|
| `EstadoComprobante` | `EMITIDO`, `ANULADO`, `RECHAZADO` |
| `TipoComprobante` | `FACTURA = "01"`, `BOLETA = "03"` |

---

### 1.3 Servicios de Dominio (`app/domain/services/`)

#### `ComprobanteDomainService` (`comprobante_domain_service.py`)
| Método | Descripción |
|--------|-------------|
| `calcular_totales(items)` | Retorna `{subtotal, igv, total}` sumando todos los items |
| `validar_montos(comprobante)` | Lanza error si `total <= 0` o algún item tiene precio negativo |

---

### 1.4 Puertos (Interfaces) (`app/domain/ports/`)

#### Inbound: `ComprobanteService` (`inbound/comprobante_service.py`)
| Método | Descripción |
|--------|-------------|
| `emitir_boleta(dto)` | Abstracto — emite boleta |
| `emitir_factura(dto)` | Abstracto — emite factura |
| `consultar(id)` | Abstracto — consulta comprobante |
| `anular(id, motivo)` | Abstracto — anula comprobante |

#### Outbound: `ComprobanteRepository` (`outbound/comprobante_repo.py`)
| Método | Descripción |
|--------|-------------|
| `save(comprobante)` | Guarda nuevo comprobante |
| `find_by_id(id)` | Busca por UUID |
| `find_by_serie_correlativo(ruc, serie, correlativo, tipo)` | Busca por serie+correlativo |
| `update(comprobante)` | Actualiza comprobante existente |
| `delete(id)` | Elimina comprobante |

#### Outbound: `SunatGateway` (`outbound/sunat_gateway.py`)
| Método | Descripción |
|--------|-------------|
| `send_bill(zip_bytes, filename)` | Envía comprobante ZIP a SUNAT → `CdrResponse` |
| `get_status(ticket)` | Consulta estado de ticket → `CdrResponse` |
| `send_summary(zip_bytes, filename)` | Envía resumen diario → `CdrResponse` |

#### Outbound: `XmlSigner` (`outbound/xml_signer.py`)
| Método | Descripción |
|--------|-------------|
| `sign(xml_string, private_key, certificate)` | Firma XML digitalmente → string firmado |

#### `CdrResponse` (dataclass, `outbound/sunat_gateway.py`)
| Atributo | Tipo | Descripción |
|----------|------|-------------|
| `codigo_respuesta` | `str` | "0" = aceptado, otros = error |
| `descripcion` | `str` | Descripción de la respuesta |
| `cdr_bytes` | `bytes?` | CDR en bruto (ZIP) |
| `observaciones` | `str?` | Observaciones del CDR |

---

## 2. Capa de Aplicación (`app/application/`)

### 2.1 DTOs (`app/application/dtos/`)

#### `ItemDTO` (`boleta_dto.py`)
| Atributo | Descripción |
|----------|-------------|
| `descripcion`, `cantidad`, `precio_unitario`, `igv_porcentaje`, `unidad_medida` | Mismos campos que `Item` del dominio |

#### `EmitirBoletaRequest` (`boleta_dto.py`)
| Atributo | Descripción |
|----------|-------------|
| `ruc_emisor`, `serie`, `correlativo`, `moneda`, `items` | Datos de emisión |
| `tipo_doc_cliente`, `num_doc_cliente`, `nombre_cliente` | Datos del cliente (opcionales) |

#### `EmitirBoletaResponse` (`boleta_dto.py`)
| Atributo | Descripción |
|----------|-------------|
| `id`, `xml_firmado_b64`, `hash_cpe`, `cdr_codigo`, `cdr_descripcion`, `cdr_observaciones`, `estado` | Resultado de emisión |

#### `EmitirFacturaRequest` (`factura_dto.py`)
| Atributo | Descripción |
|----------|-------------|
| `ruc_emisor`, `serie`, `correlativo`, `moneda`, `items` | Datos de emisión |
| `ruc_receptor`, `razon_social_receptor` | Datos del receptor |
| `tipo_doc_cliente`, `num_doc_cliente`, `nombre_cliente` | Datos del cliente (opcionales) |

#### `EmitirFacturaResponse` (`factura_dto.py`)
| Atributo | Descripción |
|----------|-------------|
| `id`, `xml_firmado_b64`, `hash_cpe`, `cdr_codigo`, `cdr_descripcion`, `cdr_observaciones`, `estado` | Resultado de emisión |

#### `ComprobanteDetalleResponse` (`response_dto.py`)
- Todos los campos del comprobante + `items` con subtotales computados
- `ruc_receptor`, `razon_social_receptor` (solo factura)
- `tipo_doc_cliente`, `num_doc_cliente`, `nombre_cliente` (boleta y factura)
- Totales: `total_subtotal`, `total_igv`, `total`
- Timestamps: `created_at`, `updated_at`

#### `AnulacionResponse` (`response_dto.py`)
| Atributo | Descripción |
|----------|-------------|
| `id`, `estado`, `cdr_codigo`, `cdr_descripcion`, `cdr_observaciones`, `motivo` | Resultado de anulación |

---

### 2.2 Casos de Uso (`app/application/use_cases/`)

#### `EmitirBoletaUseCase` (`emitir_boleta.py`)
| Método | Descripción |
|--------|-------------|
| `__init__(xml_signer, sunat_gateway, repo, ubl_builder, zip_service, private_key, certificate)` | Inyecta dependencias |
| `emitir_boleta(dto)` | **Flujo completo:** (1) crear VOs y Boleta → (2) validar montos → (3) calcular totales → (4) generar XML → (5) firmar XML → (6) base64 y hash → (7) comprimir ZIP → (8) enviar a SUNAT → (9) procesar CDR → (10) marcar emitido → (11) guardar en repo → (12) retornar respuesta |
| `emitir_factura(dto)` | Lanza `NotImplementedError` |
| `consultar(id)` | Lanza `NotImplementedError` |
| `anular(id, motivo)` | Lanza `NotImplementedError` |
| `_map_items(items_dto)` | Convierte lista `ItemDTO` → `Item` del dominio |

#### `EmitirFacturaUseCase` (`emitir_factura.py`)
| Método | Descripción |
|--------|-------------|
| `emitir_factura(dto)` | Mismo flujo que boleta pero con `Factura` en vez de `Boleta` y usando `build_factura()` |
| `emitir_boleta(dto)` | Lanza `NotImplementedError` |
| `consultar(id)` | Lanza `NotImplementedError` |
| `anular(id, motivo)` | Lanza `NotImplementedError` |
| `_map_items(items_dto)` | Convierte lista `ItemDTO` → `Item` del dominio |

#### `ConsultarComprobanteUseCase` (`consultar_comprobante.py`)
| Método | Descripción |
|--------|-------------|
| `__init__(repo)` | Inyecta repositorio |
| `consultar(id)` | Busca por ID en repo, mapea a `ComprobanteDetalleResponse` con items y campos específicos según tipo (Factura/Boleta) |
| `_to_response(c)` | Convierte entidad a DTO de respuesta, extrayendo `ruc_receptor` para facturas y datos de cliente para ambos |

#### `AnularComprobanteUseCase` (`anular_comprobante.py`)
| Método | Descripción |
|--------|-------------|
| `__init__(repo, xml_signer, sunat_gateway, ubl_builder, zip_service, private_key, certificate)` | Inyecta dependencias |
| `anular(id, motivo)` | (1) busca comprobante → (2) `comprobante.anular(motivo)` → (3) genera XML anulación → (4) firma → (5) comprime ZIP → (6) envía a SUNAT → (7) actualiza CDR → (8) `repo.update()` → (9) retorna `AnulacionResponse` |

---

## 3. Capa de Infraestructura (`app/infrastructure/`)

### 3.1 Generación XML (`app/infrastructure/xml/ubl21_builder.py`)

#### `Ubl21Builder`
| Método | Descripción |
|--------|-------------|
| `__init__(razon_social)` | Configura razón social del emisor |
| `_make_doc(tag, ns, text)` | Crea elemento XML `{ns}tag` con texto opcional |
| `_make_q(tag, ns)` | Retorna `{ns}tag` (qualified name) |
| `_build_UBLExtensions(root)` | Agrega `<ext:UBLExtensions><ext:UBLExtension><ext:ExtensionContent/>` (placeholder para firma digital) |
| `_build_header(root, comprobante)` | Agrega UBLVersionID="2.1", CustomizationID="2.0", ID (serie-correlativo), IssueDate, IssueTime, InvoiceTypeCode (01/03), DocumentCurrencyCode |
| `_build_signature(root, comprobante)` | Agrega `<cac:Signature>` con ID="IDSignSG", SignatoryParty vacío y DigitalSignatureAttachment apuntando a `#IDSignSG` |
| `_build_accounting_supplier(root, comprobante)` | Agrega AccountingSupplierParty con RUC (schemeID="6"), PartyName y RegistrationName |
| `_build_tax_total(root, comprobante, igv, subtotal)` | Agrega TaxTotal global con TaxAmount, TaxSubtotal (base imponible, monto), TaxCategory (ID="S", Percent="18.00", TaxScheme ID="1000" IGV VAT) |
| `_build_legal_monetary_total(root, comprobante, subtotal, total)` | Agrega LegalMonetaryTotal con LineExtensionAmount, TaxInclusiveAmount, ChargeTotalAmount="0.00", PayableAmount |
| `_build_items(root, items, comprobante)` | Por cada item: InvoiceLine con InvoicedQuantity, LineExtensionAmount, PricingReference (AlternativeConditionPrice), TaxTotal por item (TaxCategory con Percent dinámico), Item (Description), Price (PriceAmount) |
| `build_boleta(comprobante, subtotal, igv, total)` | **Construye XML completo de Invoice UBL 2.1**: raíz `<Invoice>` con namespaces → UBLExtensions → Header → Signature → AccountingSupplierParty → AccountingCustomerParty (si hay cliente) → TaxTotal → LegalMonetaryTotal → InvoiceLines |
| `build_factura(...)` | **Delega a `build_boleta()`** — misma estructura XML |
| `build_anulacion(comprobante, motivo)` | Construye XML simplificado: UBLExtensions → Header (InvoiceTypeCode="01") → Signature → AccountingSupplierParty → BillingReference > InvoiceDocumentReference (ID del documento original) |

**Namespaces utilizados:**
| Prefijo | URI |
|---------|-----|
| `cbc` | `urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2` |
| `cac` | `urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2` |
| `ext` | `urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2` |
| `ds` | `http://www.w3.org/2000/09/xmldsig#` |
| `xsi` | `http://www.w3.org/2001/XMLSchema-instance` |
| `sac` | `urn:sunat:names:specification:ubl:peru:schema:xsd:SunatAggregateComponents-1` |

---

### 3.2 Firma Digital XML (`app/infrastructure/xml/xml_signer_adapter.py`)

#### `XmlSignerAdapter`
| Método | Descripción |
|--------|-------------|
| `sign(xml_string, private_key, certificate)` | (1) parsea XML con lxml → (2) busca `<ext:ExtensionContent>` → (3) crea nodo `ds:Signature` con xmlsec (canonicalización ExclC14N, RSA-SHA256, referencia URI="" con transform Enveloped+ExclC14N, digest SHA256) → (4) agrega KeyInfo > X509Data → (5) exporta private_key a PEM, certificate a PEM → (6) carga en xmlsec.Key → (7) firma con SignatureContext → (8) retorna XML string con firma embebida |

---

### 3.3 Carga de Certificado (`app/infrastructure/certificate/pfx_loader.py`)

#### `load_pfx(pfx_path, password)` → `(private_key, certificate)`
| Paso | Descripción |
|------|-------------|
| 1 | Lee archivo `.pfx` en binario |
| 2 | Usa `cryptography.hazmat.pkcs12.load_key_and_certificates()` |
| 3 | Valida que existan private_key y certificate |
| 4 | Captura error de contraseña incorrecta |

---

### 3.4 Compresión ZIP (`app/infrastructure/zip/zip_service.py`)

#### `ZipService`
| Método | Descripción |
|--------|-------------|
| `compress(xml_string, base_filename)` | Crea ZIP en memoria con `{base_filename}.xml` adentro, retorna `(bytes, "{base_filename}.zip")` |
| `extract_xml(zip_bytes)` | Extrae el primer `.xml` del ZIP, retorna string |

---

### 3.5 SOAP SUNAT (`app/infrastructure/sunat/sunat_soap_adapter.py`)

#### `SunatSoapAdapter`
| Método | Descripción |
|--------|-------------|
| `__init__()` | Configura endpoint beta/producción, credenciales SOL |
| `_get_client()` | Crea cliente zeep con WSDL local, autenticación HTTPBasic + UsernameToken WSSE |
| `_do_request(method, **kwargs)` | Ejecuta llamada SOAP, captura `zeep.exceptions.Fault` y `requests.RequestException` |
| `send_bill(zip_bytes, filename)` | Base64 del ZIP → llama `sendBill(fileName, contentFile)` |
| `get_status(ticket)` | Llama `getStatus(ticket)` |
| `send_summary(zip_bytes, filename)` | Base64 del ZIP → llama `sendSummary(fileName, contentFile)` |
| `_parse_response(response)` | Procesa respuesta: si es bytes → CDR directo; si es SOAP → serializa a dict, extrae `codigoRespuesta`, `descripcion`, `archivo`/`cdr`/`content` (base64 o bytes), retorna `CdrResponse` |

**Endpoints** (`sunat_endpoints.py`):
| Entorno | URL |
|---------|-----|
| Beta | `https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService?wsdl` |
| Producción | `https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService?wsdl` |

---

### 3.6 Persistencia

#### `ComprobanteModel` (`models.py`) — SQLAlchemy ORM
| Columna | Tipo | Descripción |
|---------|------|-------------|
| `id` | `String(36)` PK | UUID |
| `ruc_emisor` | `String(11)` | RUC emisor |
| `serie` | `String(4)` | Serie (F001/B001) |
| `correlativo` | `Integer` | Número correlativo |
| `tipo` | `String(2)` | "01" o "03" |
| `fecha_emision` | `DateTime` | Fecha de emisión |
| `moneda` | `String(3)` | PEN/USD/EUR |
| `estado` | `String(20)` | EMITIDO/ANULADO/RECHAZADO |
| `items` | `Text` | JSON con lista de items |
| `tipo_doc_cliente`, `num_doc_cliente`, `nombre_cliente` | Opcionales | Datos del cliente |
| `ruc_receptor`, `razon_social_receptor` | Opcionales | Solo factura |
| `xml_firmado_b64`, `hash_cpe` | `Text`, `String(64)` | XML firmado y hash |
| `cdr_xml_b64`, `cdr_codigo`, `cdr_descripcion`, `cdr_observaciones` | Opcionales | CDR de SUNAT |
| `motivo_anulacion` | `String(100)` | Motivo si está anulado |
| `created_at`, `updated_at` | `DateTime` | Timestamps |

**Restricciones:** Unique `(ruc_emisor, serie, correlativo, tipo)`. Índices en `estado` y `fecha_emision`.

#### `Database` (`database.py`)
| Función | Descripción |
|---------|-------------|
| `init_db()` | Crea todas las tablas en BD |
| `get_session()` | Generador async que yield sesiones SQLAlchemy |

#### `SqliteRepository` (`sqlite_repo.py`) — Implementa `ComprobanteRepository`
| Método | Descripción |
|--------|-------------|
| `save(comprobante)` | Convierte entidad a `ComprobanteModel` (items como JSON), inserta, commitea |
| `find_by_id(id)` | Busca por UUID, convierte modelo de vuelta a entidad (Boleta o Factura según tipo) |
| `find_by_serie_correlativo(ruc, serie, correlativo, tipo)` | Busca por clave única |
| `update(comprobante)` | Obtiene modelo existente, actualiza campos, commitea |
| `delete(id)` | Elimina por ID |
| `_to_model(c)` | Mapea entidad → ORM: items como `List[Dict]` con Decimal→string, campos extra según Boleta/Factura |
| `_to_entity(m)` | Mapea ORM → entidad: items como `List[Item]`, crea Boleta o Factura según `tipo` |
| `_items_to_dict(items)` | Serializa items a `list[dict]` con Decimal como string |
| `_items_from_dict(data)` | Deserializa items desde dicts |

---

## 4. Capa API (`app/api/`)

### 4.1 Dependencias (`app/api/dependencies.py`)

| Función | Descripción |
|---------|-------------|
| `_get_certificate()` | Carga PFX una sola vez (cached) |
| `_get_xml_signer()` | Singleton de `XmlSignerAdapter` |
| `_get_sunat_gateway()` | Singleton de `SunatSoapAdapter` |
| `_get_ubl_builder()` | Singleton de `Ubl21Builder` |
| `_get_zip_service()` | Singleton de `ZipService` |
| `get_repo(session)` | Crea `SqliteRepository` por request |
| `get_emitir_boleta_use_case(repo)` | Wires todas las dependencias para boleta |
| `get_emitir_factura_use_case(repo)` | Wires todas las dependencias para factura |
| `get_consultar_use_case(repo)` | Solo necesita repo |
| `get_anular_use_case(repo)` | Wires todas las dependencias para anulación |

### 4.2 Schemas Pydantic (`app/api/v1/schemas/`)

#### `ItemSchema` (`boleta_schema.py`)
- Valida `descripcion` (1-500 chars), `cantidad` (>0), `precio_unitario` (>=0), `igv_porcentaje` (0-1), `unidad_medida` (1-4 chars)

#### `BoletaSchema` (`boleta_schema.py`)
- `ruc_emisor` (11 dígitos + checksum), `serie` (B001-B999), `correlativo` (1-99999999)
- `moneda` (PEN/USD/EUR), `items` (min 1)
- `tipo_doc_cliente` (1|6), `num_doc_cliente`, `nombre_cliente` (opcionales)
- Validadores: RUC checksum, formato serie, consistencia tipo_doc con num_doc

#### `FacturaSchema` (`factura_schema.py`)
- Campos de boleta + `ruc_receptor` (11 dígitos + checksum), `razon_social_receptor` (1-200 chars)
- Serie debe empezar con "F"

### 4.3 Routers FastAPI

#### `boletas.py` (`/api/v1/boletas`)
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `POST /` | `emitir_boleta()` | Valida con `BoletaSchema` → mapea a `EmitirBoletaRequest` → ejecuta use case → retorna `BoletaResponse` (201) |

#### `facturas.py` (`/api/v1/facturas`)
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `POST /` | `emitir_factura()` | Valida con `FacturaSchema` → mapea a `EmitirFacturaRequest` → ejecuta use case → retorna `FacturaResponse` (201) |

#### `consultas.py` (`/api/v1/comprobantes`)
| Endpoint | Método | Descripción |
|----------|--------|-------------|
| `GET /health` | `health()` | Retorna estado y entorno (beta/producción) |
| `GET /{id}` | `consultar_comprobante()` | Busca comprobante por ID, retorna detalle completo (404 si no existe) |
| `POST /{id}/anular` | `anular_comprobante()` | Anula comprobante con motivo (400 si error de validación) |

---

## 5. Flujo Completo de Emisión (Boleta y Factura)

```
POST /api/v1/boletas (o /facturas)
  │
  ├── [API] BoletaSchema/FacturaSchema valida request
  │     • RUC checksum, formato serie, items > 0, moneda válida
  │
  ├── [API] Router → mapea a DTO (EmitirBoletaRequest / EmitirFacturaRequest)
  │
  ├── [DI] Inyecta dependencias (certificado, firmante, SOAP, builder, ZIP, repo)
  │
  ├── [UseCase] EmitirBoletaUseCase.emitir_boleta() / EmitirFacturaUseCase.emitir_factura()
  │     │
  │     ├── Crear Value Objects: Ruc, SerieCorrelativo, Moneda
  │     ├── Crear Items del dominio
  │     ├── Crear entidad Boleta/Factura
  │     ├── Validar montos (ComprobanteDomainService)
  │     ├── Calcular totales (ComprobanteDomainService)
  │     │
  │     ├── [Infra] Ubl21Builder.build_boleta() / build_factura()
  │     │     → XML UBL 2.1 (Invoice) con cabecera, emisor, cliente,
  │     │       impuestos, totales, items, placeholder para firma
  │     │
  │     ├── [Infra] XmlSignerAdapter.sign()
  │     │     → Firma digital (RSA-SHA256, envolvente, ExclC14N)
  │     │     → Firma embebida en <ext:ExtensionContent>
  │     │
  │     ├── Base64(xml_firmado) → xml_firmado_b64
  │     ├── SHA256(xml_firmado) → hash_cpe (hex mayúscula)
  │     │
  │     ├── [Infra] ZipService.compress() → ZIP en memoria
  │     │
  │     ├── [Infra] SunatSoapAdapter.send_bill()
  │     │     → SOAP con WSSE UsernameToken
  │     │     → sendBill(fileName, contentFile=base64(ZIP))
  │     │     → Retorna CdrResponse (código, descripción, CDR bytes)
  │     │
  │     ├── Procesar CDR: base64(cdr_bytes) → cdr_xml_b64
  │     ├── comprobante.marcar_emitido(...)
  │     │
  │     └── [Infra] SqliteRepository.save()
  │           → Convierte a ORM (items como JSON)
  │           → INSERT en tabla comprobantes
  │           → COMMIT
  │
  └── Retorna BoletaResponse/FacturaResponse (201 Created)
```

### Diferencias Boleta vs Factura

| Aspecto | Boleta | Factura |
|---------|--------|---------|
| Endpoint | `POST /api/v1/boletas` | `POST /api/v1/facturas` |
| Schema | `BoletaSchema` | `FacturaSchema` |
| Serie | B001-B999 | F001-F999 |
| Entidad | `Boleta` | `Factura` |
| `tipo` | `"03"` | `"01"` |
| Requiere RUC receptor | No | Sí |
| Requiere razón social receptor | No | Sí |
| Build XML | `build_boleta()` | `build_factura()` (delega a `build_boleta()`) |
| Use Case | `EmitirBoletaUseCase` | `EmitirFacturaUseCase` |

---

## 6. Flujo de Consulta

```
GET /api/v1/comprobantes/{id}
  │
  ├── [UseCase] ConsultarComprobanteUseCase.consultar(id)
  │     ├── SqliteRepository.find_by_id(id)
  │     │     → Consulta SQL por UUID
  │     │     → Convierte modelo ORM a Boleta o Factura según tipo
  │     └── Mapea a ComprobanteDetalleResponse
  │           → Items con subtotal/igv/total computados
  │           → ruc_receptor solo si es Factura
  │           → datos de cliente para Boleta y Factura
  │
  └── Retorna ComprobanteDetalleOut (200 OK)
```

---

## 7. Flujo de Anulación

```
POST /api/v1/comprobantes/{id}/anular
  Body: {"motivo": "..."}
  │
  ├── [API] AnulacionBody valida motivo (5-100 chars)
  │
  ├── [UseCase] AnularComprobanteUseCase.anular(id, motivo)
  │     ├── repo.find_by_id(id) → busca comprobante
  │     ├── comprobante.anular(motivo) → estado = ANULADO
  │     ├── Ubl21Builder.build_anulacion()
  │     │     → XML simplificado con BillingReference al documento original
  │     ├── XmlSignerAdapter.sign() → firma XML
  │     ├── ZipService.compress() → ZIP
  │     ├── SunatSoapAdapter.send_bill() → envía a SUNAT
  │     ├── Actualiza CDR en entidad
  │     ├── repo.update() → persiste cambios
  │     └── Retorna AnulacionResponse
  │
  └── Retorna AnulacionResponse (200 OK)
```

---

## 8. Configuración (`app/config.py`)

| Variable | Default | Descripción |
|----------|---------|-------------|
| `sunat_env` | `"beta"` | Entorno SUNAT |
| `sunat_ruc` | `""` | RUC del emisor |
| `sunat_usuario_sol` | `""` | Usuario SOL |
| `sunat_clave_sol` | `""` | Clave SOL |
| `pfx_path` | `"./certificados/certificado.pfx"` | Ruta del certificado digital |
| `pfx_password` | `""` | Contraseña del PFX |
| `api_secret_key` | `""` | Clave secreta API |
| `database_url` | `"sqlite+aiosqlite:///./sunat.db"` | URL de base de datos |
| `is_produccion` (property) | — | `True` si `sunat_env == "produccion"` |

---

## 9. Índice de Archivos

| Archivo | Rol |
|---------|-----|
| `app/main.py` | Punto de entrada FastAPI, registro de routers |
| `app/config.py` | Configuración vía pydantic-settings |
| `app/api/dependencies.py` | Wireado de dependencias (DI) |
| `app/api/v1/routers/boletas.py` | Endpoint POST boleta |
| `app/api/v1/routers/facturas.py` | Endpoint POST factura |
| `app/api/v1/routers/consultas.py` | Endpoints GET/{id}, POST/{id}/anular, GET/health |
| `app/api/v1/schemas/boleta_schema.py` | Validación Pydantic para boleta |
| `app/api/v1/schemas/factura_schema.py` | Validación Pydantic para factura |
| `app/domain/entities/comprobante.py` | Entidad base Comprobante, Item, enums |
| `app/domain/entities/boleta.py` | Entidad Boleta (hereda Comprobante) |
| `app/domain/entities/factura.py` | Entidad Factura (hereda Comprobante) |
| `app/domain/value_objects/ruc.py` | Value Object RUC con validación |
| `app/domain/value_objects/moneda.py` | Enum Moneda (PEN/USD/EUR) |
| `app/domain/value_objects/serie_correlativo.py` | Value Object SerieCorrelativo |
| `app/domain/services/comprobante_domain_service.py` | Validación y cálculos de dominio |
| `app/domain/ports/inbound/comprobante_service.py` | Puerto de entrada (interfaz use case) |
| `app/domain/ports/outbound/comprobante_repo.py` | Puerto de repositorio |
| `app/domain/ports/outbound/sunat_gateway.py` | Puerto de gateway SUNAT + CdrResponse |
| `app/domain/ports/outbound/xml_signer.py` | Puerto de firmante XML |
| `app/application/dtos/boleta_dto.py` | DTOs: ItemDTO, EmitirBoletaRequest/Response |
| `app/application/dtos/factura_dto.py` | DTOs: EmitirFacturaRequest/Response |
| `app/application/dtos/response_dto.py` | DTOs: ComprobanteDetalleResponse, AnulacionResponse |
| `app/application/use_cases/emitir_boleta.py` | Caso de uso: emitir boleta |
| `app/application/use_cases/emitir_factura.py` | Caso de uso: emitir factura |
| `app/application/use_cases/consultar_comprobante.py` | Caso de uso: consultar comprobante |
| `app/application/use_cases/anular_comprobante.py` | Caso de uso: anular comprobante |
| `app/infrastructure/xml/ubl21_builder.py` | Generación de XML UBL 2.1 |
| `app/infrastructure/xml/xml_signer_adapter.py` | Firma digital XML con xmlsec |
| `app/infrastructure/zip/zip_service.py` | Compresión/descompresión ZIP |
| `app/infrastructure/sunat/sunat_soap_adapter.py` | Cliente SOAP para SUNAT |
| `app/infrastructure/sunat/sunat_endpoints.py` | Endpoints beta/producción |
| `app/infrastructure/certificate/pfx_loader.py` | Carga de certificado PFX |
| `app/infrastructure/persistence/database.py` | Engine SQLAlchemy async, sesiones |
| `app/infrastructure/persistence/models.py` | Modelo ORM ComprobanteModel |
| `app/infrastructure/persistence/sqlite_repo.py` | Implementación repositorio SQLite |
