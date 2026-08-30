# 08 — QA/QC y validación

## QA del CSV

Recalcular:
- filas;
- columnas;
- delimiter/encoding;
- nulos;
- duplicados;
- rango espacial;
- timestamp;
- comuna/región;
- superficies;
- temperaturas;
- RH;
- viento;
- pendiente;
- combustible;
- causas.

No borrar outliers sin conservar:
- valor original;
- regla;
- flag;
- decisión.

## QA geográfico

- coordenadas plausibles;
- continente/islas;
- Codcom vs punto;
- duplicados espaciales/temporales;
- precisión aparente.

## QA temporal

- orden Inicio/Detección/Aviso/etc.;
- timezones;
- daylight saving;
- fechas meteorológicas;
- temporada.

## Leakage tests automatizados

Cada feature debe tener `available_at`.

Fail si:
```text
available_at > prediction_time
```

para entrenamiento de P-IGN.

## Validación temporal

Train/validation/test fijo inicialmente.

## Validación espacial

- leave-region-out;
- bloques espaciales;
- métricas por región;
- métricas por combustible.

## Calibración

Reliability bins + Brier.

Publicar P solo después de calibración.

## Baseline regression

Fixtures deben bloquear cambios accidentales.

## Forecast backtest

Usar cycle + lead correcto.

No usar condiciones observadas para afirmar skill forecast.

## Reportes estándar

Cada modelo:
- dataset version;
- split;
- features;
- tuning;
- métricas;
- calibration;
- subgroup metrics;
- mapa de errores;
- limitaciones;
- model card.
