"""
src/api/routes.py — Definición de rutas y controladores REST para la API de BR-HR.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, status

from src.api.schemas import (
    CommuneForecastResponse,
    ForecastSummaryResponse,
    H3CellForecastResponse,
    HealthResponse,
    TriggerForecastRequest,
    TriggerForecastResponse,
)
from src.api.services import forecast_service

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Estado de salud de la API",
    tags=["Monitoreo"],
)
async def health_check() -> HealthResponse:
    """Verifica el estado operativo del servicio, conexión a Earth Engine y último pronóstico."""
    data = forecast_service.get_health()
    return HealthResponse(**data)


@router.get(
    "/api/v1/forecast/latest/summary",
    response_model=ForecastSummaryResponse,
    summary="Resumen nacional de alertas Botón Rojo",
    tags=["Pronóstico"],
)
async def get_latest_summary() -> ForecastSummaryResponse:
    """Retorna métricas agregadas a nivel país: total de hexágonos en alerta roja, amarilla y ranking de comunas."""
    try:
        data = forecast_service.get_summary()
        return ForecastSummaryResponse(**data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo resumen de pronóstico: {str(e)}",
        )


@router.get(
    "/api/v1/forecast/latest/communes",
    response_model=List[CommuneForecastResponse],
    summary="Listado de comunas con porcentaje de Botón Rojo",
    tags=["Comunas"],
)
async def get_all_communes(
    region: Optional[str] = Query(None, description="Filtrar por nombre de región (ej: Biobío, Valparaíso)"),
    alert_level: Optional[str] = Query(None, description="Filtrar por nivel de alerta (ROJO, AMARILLO, VERDE)"),
) -> List[CommuneForecastResponse]:
    """Retorna todas las comunas de Chile con su porcentaje de superficie bajo Botón Rojo y nivel de alerta."""
    data = forecast_service.get_communes(region=region, alert_level=alert_level)
    return [CommuneForecastResponse(**c) for c in data]


@router.get(
    "/api/v1/forecast/latest/commune/{comuna_name}",
    summary="Detalle de alerta para una comuna específica",
    tags=["Comunas"],
)
async def get_commune_detail(comuna_name: str) -> Dict[str, Any]:
    """Retorna las estadísticas detalladas y las celdas H3 asociadas a una comuna determinada."""
    data = forecast_service.get_commune_detail(comuna_name)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comuna '{comuna_name}' no encontrada en el pronóstico actual.",
        )
    return data


@router.get(
    "/api/v1/forecast/latest/h3/{h3_id}",
    response_model=H3CellForecastResponse,
    summary="Consulta de riesgo de un hexágono H3 específico",
    tags=["Hexágonos H3"],
)
async def get_h3_cell_forecast(h3_id: str) -> H3CellForecastResponse:
    """Retorna los valores de riesgo (horas Botón Rojo, p_ignición, p_gran_incendio) de un hexágono H3 (resolución 8)."""
    data = forecast_service.get_h3_cell(h3_id)
    if not data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hexágono H3 '{h3_id}' no encontrado.",
        )
    return H3CellForecastResponse(**data)


@router.get(
    "/api/v1/forecast/latest/h3-geojson",
    summary="Malla GeoJSON de hexágonos H3 con riesgo inyectado",
    tags=["Geospatial / GeoLibre"],
)
async def get_h3_geojson_mesh() -> Dict[str, Any]:
    """Retorna la malla completa de 33.237 hexágonos GeoJSON con sus propiedades de riesgo para renderizado web en GeoLibre / MapLibre."""
    return forecast_service.get_h3_geojson()


@router.post(
    "/api/v1/forecast/trigger",
    response_model=TriggerForecastResponse,
    summary="Disparar corrida de inferencia diaria",
    tags=["Operacional"],
)
async def trigger_forecast_execution(
    payload: TriggerForecastRequest = TriggerForecastRequest(),
) -> TriggerForecastResponse:
    """Ejecuta el pipeline de inferencia satelital diaria y actualiza las salidas de riesgo."""
    try:
        res = forecast_service.trigger_forecast(
            target_date=payload.target_date,
            use_live_gee=payload.use_live_gee,
        )
        return TriggerForecastResponse(**res)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo al ejecutar pronóstico: {str(e)}",
        )


@router.get(
    "/api/v1/firms/active-points",
    summary="Anomalías térmicas satelitales en tiempo real (NASA FIRMS / VIIRS 375m)",
    tags=["Satelital / Tiempo Real"],
)
async def get_firms_active_points(
    days: int = Query(1, ge=1, le=5, description="Número de días hacia atrás (1 a 5 días)"),
) -> Dict[str, Any]:
    """Retorna los focos de calor satelitales NRT de las últimas 24 a 72 horas detectados por VIIRS (375m) y MODIS."""
    from src.api.firms_service import firms_service
    return firms_service.get_active_fires(days=days)

