# Guía de Arquitectura y Despliegue del Backend BR-HR (FastAPI / Railway)

**Módulo:** `src.api` (Fase 9 del Plan de Desarrollo)  
**Tecnología:** Python 3.11+, FastAPI, Uvicorn, Pydantic v2, Google Earth Engine API, Apache Arrow / Parquet.

---

## 1. Arquitectura del Backend

La API de BR-HR proporciona una capa desacoplada, ligera y de alta velocidad (<20 ms por consulta) para servir los pronósticos de riesgo de incendios forestales a nivel subcomunal (hexágonos Uber H3 Resolución 8, ~74 ha) y comunal.

```
                  ┌──────────────────────────────────────────────┐
                  │          Google Earth Engine (GEE)           │
                  │   NOAA GFS / ERA5 / ESA / Dynamic World      │
                  └──────────────────────┬───────────────────────┘
                                         │ Inferencia diaria (GEE Pipeline)
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │       Data Lake / In-Memory Cache            │
                  │  * br_hr_h3_latest.parquet (33.237 hex)      │
                  │  * br_hr_communes_latest.json (346 comunas)  │
                  └──────────────────────┬───────────────────────┘
                                         │
                                         ▼
                  ┌──────────────────────────────────────────────┐
                  │             FastAPI Backend (src.api)        │
                  │  - /health                                   │
                  │  - /api/v1/forecast/latest/summary           │
                  │  - /api/v1/forecast/latest/communes          │
                  │  - /api/v1/forecast/latest/h3/{h3_id}        │
                  │  - /api/v1/forecast/latest/h3-geojson        │
                  └──────────────┬───────────────────────────────┘
                                 │ REST JSON / GeoJSON
                                 ▼
                  ┌──────────────────────────────────────────────┐
                  │     Frontend / GeoLibre / SENAPRED / CONAF   │
                  └──────────────────────────────────────────────┘
```

---

## 2. Catálogo de Endpoints REST

| Método | Endpoint | Descripción | Respuesta |
|:---:|---|---|---|
| `GET` | `/health` | Estado del servicio y conexión a Google Earth Engine | `HealthResponse` |
| `GET` | `/api/v1/forecast/latest/summary` | Resumen nacional de celdas en alerta y ranking comunal | `ForecastSummaryResponse` |
| `GET` | `/api/v1/forecast/latest/communes` | Listado completo de comunas con `%` de Botón Rojo | `List[CommuneForecastResponse]` |
| `GET` | `/api/v1/forecast/latest/commune/{name}` | Detalle comunal con todas sus celdas H3 asociadas | `Dict[str, Any]` |
| `GET` | `/api/v1/forecast/latest/h3/{h3_id}` | Consulta puntual de un hexágono H3 (Res 8) | `H3CellForecastResponse` |
| `GET` | `/api/v1/forecast/latest/h3-geojson` | Malla territorial GeoJSON con riesgo inyectado | `GeoJSON FeatureCollection` |
| `POST` | `/api/v1/forecast/trigger` | Disparador de la corrida de inferencia diaria | `TriggerForecastResponse` |

---

## 3. Ejecución en Entorno Local

Para iniciar el servidor local de desarrollo:

```bash
# Opción 1: Ejecutar con uvicorn directamente
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Opción 2: Ejecutar el módulo main
python -m src.api.main
```

Acceder a la documentación interactiva Swagger:
* 👉 **Swagger UI:** `http://localhost:8000/docs`
* 👉 **ReDoc:** `http://localhost:8000/redoc`

---

## 4. Despliegue en Railway (Paso a Paso)

1. **Crear Proyecto en Railway:**
   * Entra a [railway.app](https://railway.app/) y selecciona **New Project** > **Deploy from GitHub repo**.
   * Selecciona el repositorio `BOTON_Rojo_Chile`.

2. **Configuración Automática:**
   * Railway detectará automáticamente el archivo [`Dockerfile`](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/Dockerfile) y [`railway.json`](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/railway.json).
   * El puerto dinámico (`$PORT`) es administrado automáticamente por Uvicorn.

3. **Variables de Entorno en Railway (Variables de Entorno de Producción):**
   * En la pestaña **Variables** de Railway, agregar:
     * `GEE_SERVICE_ACCOUNT_JSON`: Contenido completo en texto del archivo de credenciales de Google Cloud (`boton-rojo-chile-49f6f47ffe4f.json`).
     * `PORT`: `8000` (o el asignado automáticamente).
     * `ENVIRONMENT`: `production`.

---

## 5. Verificación y Pruebas Unitarias

Para ejecutar la suite de pruebas unitarias automatizadas de la API:

```bash
python -m unittest tests/unit/test_api_endpoints.py
```
