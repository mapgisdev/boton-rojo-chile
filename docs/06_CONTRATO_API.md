# 06 — Contrato API inicial

Base sugerida:

```text
/api/v1
```

## Estado

### GET /health
Respuesta:
```json
{
  "status": "ok",
  "service": "brhr-api",
  "version": "..."
}
```

### GET /model
Devuelve champion/challenger, versión y métricas resumidas.

## Runs

### GET /runs/latest
Última corrida válida.

### GET /runs/{run_id}
Metadata completa.

Ejemplo de metadata:

```json
{
  "run_id": "BRHR_20260828_12Z_v1.0",
  "model_version": "pign-logistic-1.0",
  "input_cycle": "2026-08-28T12:00:00Z",
  "created_at": "...",
  "horizons": [0,1,2,3,4],
  "data_versions": {}
}
```

## Mapas

### GET /maps/{layer}/{horizon}
Devuelve metadata necesaria para visualizar la capa actual.

Layers:
- br_original
- br_calibrated
- p_ignition
- p_gt10ha
- p_gt100ha
- br_fraction
- wind
- fuel_moisture
- confidence

No enviar secretos/tokens permanentes del backend.

## H3

### GET /hex/{h3_id}
Parámetros:
- run_id opcional;
- horizon opcional.

Respuesta conceptual:

```json
{
  "h3_id": "...",
  "run_id": "...",
  "horizon": 1,
  "p_ignition": 0.81,
  "p_gt10ha": 0.47,
  "p_gt100ha": 0.19,
  "br_original": true,
  "br_calibrated": true,
  "br_hours": 4,
  "br_fraction": 0.76,
  "wind_p90_kmh": 31.0,
  "rh_p10_pct": 17.0,
  "fuel_fraction": 0.89,
  "dominant_fuel": "grass",
  "confidence": "high"
}
```

### GET /hex/{h3_id}/history
Serie temporal paginada.

## Comuna

### GET /communes/{codcom}
Indicadores resumidos.

### GET /communes/{codcom}/forecast
Horizontes disponibles.

## Errores

Formato único:
```json
{
  "error": {
    "code": "RUN_NOT_FOUND",
    "message": "...",
    "request_id": "..."
  }
}
```

## Reglas

- OpenAPI obligatorio.
- Schemas Pydantic/TypeScript equivalentes.
- versionado `/v1`.
- logs sin secretos.
- rate limits razonables.
- CORS explícito.
- timeouts y retry policy para Earth Engine.
- cache de metadata; no cachear eternamente URLs temporales.
