# 04 — Reporte de Calidad QA/QC y Malla Territorial H3 (Fase 2)

Fecha de generación: 29 de agosto de 2026  
Módulo: BR-HR — Ingesta, Estandarización y Malla H3 Resolución 8  
Archivos producidos:
- `data/derived/incendios_qa.parquet` (68.546 filas, 41 columnas)
- `data/derived/h3_chile_r8_index.parquet` (33.237 celdas únicas)
- `data/derived/h3_commune_weights.parquet` (33.237 ponderaciones comunales)

---

## 1. Resumen de Ingesta y Limpieza

El pipeline [`src/training/qa/dataset_cleaner.py`](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/src/training/qa/dataset_cleaner.py) procesó de manera estrictamente no destructiva el dataset original:

| Concepto | Recuento / Métrica | % sobre el total |
|---|---|---|
| **Registros totales leídos** | **68.546** | 100,00 % |
| **Registros con coordenadas válidas** | **68.536** | 99,99 % |
| **Registros con errata corregida** | **2** (Parral y Ercilla) | <0,01 % |
| **Registros con coordenadas faltantes** | **8** (`QA_MISSING_COORD`) | 0,01 % |
| **Total eventos georreferenciados a celdas H3** | **68.538** | 99,99 % |
| **Celdas H3 Resolución 8 únicas con ignición** | **33.237** | — |
| **Comunas únicas cubiertas (`Codcom`)** | **319** | — |

---

## 2. Particiones Temporales (Splits) Inmutables

| Partición | Temporadas | N° Incendios | % del Total |
|---|---|---|---|
| **TRAIN** | 2014–2015 a 2020–2021 (7 temporadas) | **48.659** | 70,99 % |
| **VALIDATION** | 2021–2022 (1 temporada) | **6.947** | 10,13 % |
| **TEST CIEGO** | 2022–2023 y 2023–2024 (2 temporadas) | **12.940** | 18,88 % |

---

## 3. Malla Territorial H3 Resolución 8

- **Resolución operacional:** H3 Resolución 8 (área promedio $\approx 73,73\ \mathrm{ha}$, radio $\approx 461\ \mathrm{m}$).
- **Resolución experimental:** H3 Resolución 9 (área promedio $\approx 10,53\ \mathrm{ha}$).
- **Archivo maestro:** [`data/derived/h3_chile_r8_index.parquet`](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/data/derived/h3_chile_r8_index.parquet).
- **Ponderación Comunal:** [`data/derived/h3_commune_weights.parquet`](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/data/derived/h3_commune_weights.parquet). La identidad hexagonal nunca se corta por límites comunales; la agregación se realiza mediante suma ponderada de intersección.

---

## 4. Esquema del Dataset Maestro Derivado (`incendios_qa.parquet`)

| Campo | Tipo | Descripción |
|---|---|---|
| `event_id` | `int64` | Identificador único reproducible (`index` original) |
| `region`, `provincia`, `comuna`, `codcom` | `string` | División política administrativa estandarizada |
| `temporada` | `string` | Temporada de ocurrencia (p.ej. "2016 al 2017") |
| `split` | `string` | Partición inmutable: `train`, `validation`, `test` |
| `lat`, `lon` | `float64` | Coordenadas decimales corregidas (WGS84) |
| `qa_coord_flag` | `string` | Flag QA: `QA_VALID`, `QA_TYPO_CORRECTED`, `QA_MISSING_COORD` |
| `h3_id` | `string` | Índice espacial H3 resolución 8 (74 ha) |
| `h3_res9_id` | `string` | Índice espacial H3 resolución 9 (10,5 ha) |
| `datetime_local` | `datetime64[ns, America/Santiago]` | Timestamp local exacto con huso horario IANA |
| `datetime_utc` | `datetime64[ns, UTC]` | Timestamp UTC para cruces satelitales y meteorológicos |
| `date_local`, `hour_local` | `date`, `int64` | Fecha y hora local de inicio |
| `in_br_window` | `bool` | `True` si inició entre 14:00 y 18:59 hora local |
| `final_area_ha` | `float64` | Superficie total quemada en hectáreas |
| `y_ignition` | `int64` | 1 (indicador de ignición positiva) |
| `y_gt10ha`, `y_gt50ha`, `y_gt100ha`, `y_gt1000ha` | `int64` | Indicadores binarios de gran incendio |
| `fuel_initial` | `string` | Combustible inicial reportado |
| `cause_general`, `cause_specific` | `string` | Clasificación de causa investigada |
| `dt_deteccion` ... `dt_extincion` | `datetime64[ns]` | Hitos de combate (solo como metadatos, no como features) |
| `flag_chrono_anomaly` | `bool` | Flag de alerta si los hitos presentan inversión temporal |
