# 05 — Plan de desarrollo por fases

## Fase 0 — Auditoría

### Entregables
- inventario legacy;
- audit del código;
- perfil CSV;
- riesgos;
- plan detallado.

### Gate
No refactor grande hasta entender/reproducir baseline.

---

## Fase 1 — Baseline reproducible

### Objetivos
- extraer legado a work;
- testear HCFM/PI/BR;
- corregir defectos técnicos sin cambiar comportamiento;
- crear golden samples.

### Aceptación
Resultados repetibles en fixtures y comparación GEE/Python.

---

## Fase 2 — QA/QC histórico + H3

### Objetivos
- normalizar tiempos;
- validar coordenadas;
- asignar H3;
- tabla H3-comuna;
- universo combustible.

### Aceptación
Reporte de calidad completo y pérdida de registros explicada.

---

## Fase 3 — MASTER_FIRE_H3 v1

### Objetivos
- positivos;
- controles;
- ERA5-Land;
- MapBiomas;
- DEM;
- features núcleo.

### Aceptación
Dataset versionado, diccionario, tests anti-leakage.

---

## Fase 4 — Recalibración BR

### Objetivos
- PI empírica;
- búsqueda de thresholds;
- comparar M0 vs M1.

### Aceptación
Mejora validación 2021–22 sin tocar test ciego.

---

## Fase 5 — Modelos probabilísticos

### Objetivos
- logistic;
- GAM;
- RF;
- gradient boosting challenger;
- calibration.

### Aceptación
Model cards + validación + modelo champion.

---

## Fase 6 — Test ciego 2022–2024

### Objetivos
Abrir test una sola vez para evaluación final.

### Aceptación
Reporte congelado sin tuning posterior silencioso.

---

## Fase 7 — Backtest forecast

### Objetivos
- GFS D+1..D+5;
- skill por horizonte;
- comparar con hindcast.

### Aceptación
Definir horizontes aptos para uso operacional.

---

## Fase 8 — Inferencia Earth Engine

### Objetivos
- portar champion;
- raster 250 m;
- H3-8;
- comuna;
- tiles.

### Aceptación
Paridad con implementación científica dentro de tolerancias.

---

## Fase 9 — API + R2

### Objetivos
- Railway;
- service account;
- endpoints;
- runs;
- históricos;
- PMTiles/Parquet.

### Aceptación
Test de contratos, secretos fuera del repo, health checks.

---

## Fase 10 — GeoLibre

### Objetivos
- capas;
- H3 popup;
- comuna;
- horizonte;
- leyenda;
- confianza;
- comparación M0/M1/P-IGN.

### Aceptación
Uso fluido a escala nacional y consultas sin geometría redundante.

---

## Fase 11 — Mejoras de alta resolución

Evaluar una por una:
- estaciones DMC/INIA;
- downscaling calibrado;
- humedad combustible con memoria;
- WRF-DMC;
- WindNinja;
- exposición humana refinada;
- H3-9 pilotos.

Solo promover si existe ganancia fuera de muestra.
