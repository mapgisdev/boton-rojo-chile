# 04 — Contrato inicial de MASTER_FIRE_H3

Cada fila representa una observación H3×timestamp.

## Identidad

| Campo | Tipo | Descripción |
|---|---|---|
| sample_id | string | identificador reproducible |
| event_id | string/null | id evento cuando sea positivo |
| h3_id | string | H3 |
| h3_resolution | int | 8 inicialmente |
| codcom | string | comuna principal / relación separada |
| region | string | región |
| sample_type | enum | positive/spatial_control/temporal_control/calibration_universe |
| sample_weight | float | peso por esquema de muestreo |
| inclusion_probability | float/null | probabilidad de inclusión si se conoce |

## Tiempo

| Campo | Tipo |
|---|---|
| datetime_local | datetime |
| timezone | string |
| datetime_utc | datetime UTC |
| date_local | date |
| hour_local | int |
| season | string |
| split | enum train/validation/test |

## Targets

- `y_ignition`
- `n_events`
- `y_gt10ha`
- `y_gt50ha`
- `y_gt100ha`
- `final_area_ha` solo para modelos posteriores, NO como feature P-IGN.

## Meteorología

- temperature_c
- dewpoint_c
- relative_humidity_pct
- vpd_kpa
- wind_speed_kmh
- wind_direction_deg
- rain_1h_mm
- rain_24h_mm
- rain_72h_mm
- rain_7d_mm
- solar_radiation
- soil_moisture

Guardar además:
- fuente;
- run/cycle cuando aplique;
- qa flag.

## Combustible

- fuel_forest_fraction
- fuel_shrub_fraction
- fuel_grass_fraction
- fuel_crop_fraction
- fuel_other_fraction
- fuel_total_fraction
- dominant_fuel
- fuel_data_year

## Vegetación

- ndvi
- ndmi
- nbr2 opcional
- ndvi_anomaly
- ndmi_anomaly
- days_since_significant_rain

## Topografía

- elevation_mean/p90
- slope_mean/p90
- aspect_circular
- northness
- eastness
- tpi
- ruggedness
- terrain_exposure

## Contexto humano

- distance_road_m
- distance_settlement_m
- wui_score si existe metodología defendible
- prior_fire_count
- prior_fire_density
- years_since_last_fire

Todo historial debe ser calculado solo con información anterior al sample.

## Baseline

- hcfm_original
- hcfm_class
- temperature_class
- exposure_class_original
- pi_original
- br_original
- br_fraction_original

## Modelo

Los predictions NO pertenecen al training table base salvo en archivos OOF separados.

- p_ignition_raw
- p_ignition_calibrated
- p_gt10ha
- p_gt100ha
- confidence

## Lineage obligatorio

Cada feature deberá tener en un diccionario:

```text
name
dtype
unit
source
source_version
spatial_resolution
temporal_resolution
availability_time
transform
null_policy
qa_rules
leakage_notes
```

## Formato

Preferir Parquet particionado:
- por split/season;
- o por año/región según benchmark.

CSV solo para muestras pequeñas o interoperabilidad.
