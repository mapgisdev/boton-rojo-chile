"""
src/api/schemas.py — Modelos Pydantic para validación y serialización de contratos REST (BR-HR API).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field("ok", description="Estado operativo de la API")
    version: str = Field("1.0.0", description="Versión de BR-HR")
    gee_connected: bool = Field(..., description="Indica si Google Earth Engine está autenticado en vivo")
    latest_forecast_date: Optional[str] = Field(None, description="Fecha del último pronóstico disponible (YYYY-MM-DD)")
    total_h3_cells: int = Field(..., description="Total de hexágonos H3 en la malla territorial")
    total_communes: int = Field(..., description="Total de comunas monitoreadas")


class AlertCountSummary(BaseModel):
    verde: int = Field(..., description="Cantidad de hexágonos en condición normal")
    temprana_preventiva: int = Field(..., description="Cantidad de hexágonos en alerta temprana preventiva")
    amarillo: int = Field(..., description="Cantidad de hexágonos en alerta amarilla")
    rojo: int = Field(..., description="Cantidad de hexágonos en Botón Rojo activo")


class ForecastSummaryResponse(BaseModel):
    date: str = Field(..., description="Fecha del pronóstico (YYYY-MM-DD)")
    generated_at: str = Field(..., description="Timestamp ISO de generación")
    total_cells: int = Field(..., description="Total de hexágonos H3 procesados")
    alert_counts: AlertCountSummary
    red_alert_percentage: float = Field(..., description="Porcentaje del territorio con Botón Rojo activo")
    top_critical_communes: List[Dict[str, Any]] = Field(..., description="Comunas con mayor porcentaje de Botón Rojo")


class H3CellForecastResponse(BaseModel):
    h3_id: str = Field(..., description="Identificador único del hexágono Uber H3 (Res 8)")
    date: str = Field(..., description="Fecha del pronóstico (YYYY-MM-DD)")
    horas_boton_rojo: int = Field(..., description="Horas continuas de Botón Rojo activo (0 a 5)")
    p_ignicion: float = Field(..., description="Probabilidad de ignición calibrada M2 [0.0 - 1.0]")
    p_gran_incendio: float = Field(..., description="Probabilidad condicional de gran incendio >10ha M3 [0.0 - 1.0]")
    alerta: str = Field(..., description="Nivel de alerta (VERDE, TEMPRANA_PREVENTIVA, AMARILLO, ROJO)")
    comuna_principal: Optional[str] = Field(None, description="Comuna a la que pertenece principalmente")
    region: Optional[str] = Field(None, description="Región administrativa")


class CommuneForecastResponse(BaseModel):
    codcom: Optional[str] = Field(None, description="Código único de la comuna")
    comuna: str = Field(..., description="Nombre oficial de la comuna")
    region: str = Field(..., description="Región administrativa")
    provincia: Optional[str] = Field(None, description="Provincia administrativa")
    total_hexagons: int = Field(..., description="Cantidad de celdas H3 en la comuna")
    red_hexagons: int = Field(..., description="Cantidad de celdas con Botón Rojo activo")
    yellow_hexagons: Optional[int] = Field(0, description="Cantidad de celdas con Alerta Amarilla")
    pct_superficie_roja: float = Field(..., description="Porcentaje de superficie comunal en Botón Rojo")
    p_ignicion_mean: float = Field(..., description="Probabilidad media de ignición")
    p_gran_incendio_max: Optional[float] = Field(0.0, description="Máxima probabilidad de gran incendio")
    alerta_comunal: str = Field(..., description="Alerta sugerida para SENAPRED (NORMAL, ALERTA TEMPRANA PREVENTIVA, ALERTA AMARILLA COMUNAL, ALERTA ROJA COMUNAL)")


class TriggerForecastRequest(BaseModel):
    target_date: Optional[str] = Field(None, description="Fecha objetivo YYYY-MM-DD (por defecto hoy)")
    use_live_gee: bool = Field(True, description="Usar conexión satelital en vivo con Google Earth Engine")


class TriggerForecastResponse(BaseModel):
    status: str = Field("success", description="Resultado de la ejecución")
    target_date: str = Field(..., description="Fecha procesada")
    processed_cells: int = Field(..., description="Hexágonos procesados")
    processed_communes: int = Field(..., description="Comunas procesadas")
    elapsed_seconds: float = Field(..., description="Tiempo total de cómputo en segundos")
