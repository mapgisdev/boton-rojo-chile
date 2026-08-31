# -*- coding: utf-8 -*-
"""
src/m0_original/meteorology/time_window.py — Gestión estacional de husos horarios y ventana 14:00–18:59.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from src.m0_original.config.constants import DIAS_PRONOSTICO, HORA_FIN, HORA_INICIO


def desfase_utc_chile(momento: datetime) -> int:
    """Calcula el desfase horario respecto a UTC para Chile continental (America/Santiago).

    Normativa (Decreto Supremo 224/2022):
    - Horario de verano (UTC-3): Desde el primer sábado de septiembre hasta el primer sábado de abril.
    - Horario estándar/invierno (UTC-4): Desde el primer sábado de abril hasta el primer sábado de septiembre.

    Parameters
    ----------
    momento : datetime
        Fecha y hora en UTC.

    Returns
    -------
    int
        Desfase horario entero (-3 o -4).
    """
    if momento.tzinfo is None:
        momento = momento.replace(tzinfo=timezone.utc)
    else:
        momento = momento.astimezone(timezone.utc)

    anio = momento.year

    def primer_sabado(mes: int) -> datetime:
        d = datetime(anio, mes, 1, 0, 0, 0, tzinfo=timezone.utc)
        return d + timedelta(days=(5 - d.weekday()) % 7)

    inicio_invierno = primer_sabado(4)
    inicio_verano = primer_sabado(9)

    if inicio_invierno <= momento < inicio_verano:
        return -4
    return -3


def horas_pronostico_ventana(corrida_utc: datetime, dias: int = DIAS_PRONOSTICO) -> List[int]:
    """Determina las horas de pronóstico GFS (f000..f120) que caen en 14:00–18:59 local.

    Parameters
    ----------
    corrida_utc : datetime
        Momento de inicio de la corrida GFS (ej. 00Z, 06Z, 12Z, 18Z).
    dias : int
        Número de días a pronosticar (por defecto 5: d0 a d4).

    Returns
    -------
    List[int]
        Horas de pronóstico GFS requeridas.
    """
    if corrida_utc.tzinfo is None:
        corrida_utc = corrida_utc.replace(tzinfo=timezone.utc)

    desfase = desfase_utc_chile(corrida_utc)
    inicio_local = corrida_utc + timedelta(hours=desfase)
    dia0 = inicio_local.date()

    requeridas = []
    for h in range(0, 121):
        valido_local = inicio_local + timedelta(hours=h)
        delta_dias = (valido_local.date() - dia0).days
        if 0 <= delta_dias < dias and HORA_INICIO <= valido_local.hour <= HORA_FIN:
            requeridas.append(h)
    return requeridas
