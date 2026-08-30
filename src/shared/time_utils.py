"""
src/shared/time_utils.py — Utilidades de manejo estricto de tiempo y zonas horarias IANA.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from zoneinfo import ZoneInfo
from typing import List, Tuple

TZ_SANTIAGO = ZoneInfo("America/Santiago")
TZ_EASTER = ZoneInfo("Pacific/Easter")
TZ_UTC = timezone.utc

BR_WINDOW_START_HOUR = 14
BR_WINDOW_END_HOUR = 18  # 18:00 to 18:59 inclusive (5 hourly steps: 14, 15, 16, 17, 18)


def to_utc(dt: datetime, default_tz: ZoneInfo = TZ_SANTIAGO) -> datetime:
    """Convierte un datetime a UTC de manera inequívoca.
    
    Si el datetime es naive, se le asigna `default_tz` antes de convertir.
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=default_tz)
    return dt.astimezone(TZ_UTC)


def to_local(dt: datetime, target_tz: ZoneInfo = TZ_SANTIAGO) -> datetime:
    """Convierte un datetime a la zona horaria local chilena especificada."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=TZ_UTC)
    return dt.astimezone(target_tz)


def is_in_br_window(dt: datetime, target_tz: ZoneInfo = TZ_SANTIAGO) -> bool:
    """Indica si el instante cae dentro de la ventana Botón Rojo (14:00 - 18:59 hora local)."""
    local_dt = to_local(dt, target_tz=target_tz)
    return BR_WINDOW_START_HOUR <= local_dt.hour <= BR_WINDOW_END_HOUR


def get_br_window_hours_for_date(d: date, target_tz: ZoneInfo = TZ_SANTIAGO) -> List[datetime]:
    """Genera los 5 datetimes locales de la ventana BR para una fecha dada (14:00 a 18:00)."""
    return [
        datetime.combine(d, time(h, 0), tzinfo=target_tz)
        for h in range(BR_WINDOW_START_HOUR, BR_WINDOW_END_HOUR + 1)
    ]


def get_utc_offset_hours(dt: datetime, target_tz: ZoneInfo = TZ_SANTIAGO) -> int:
    """Devuelve el offset UTC en horas enteras (-3 o -4 para Chile continental)."""
    local_dt = to_local(dt, target_tz=target_tz)
    offset_seconds = local_dt.utcoffset().total_seconds() if local_dt.utcoffset() else 0
    return int(offset_seconds // 3600)
