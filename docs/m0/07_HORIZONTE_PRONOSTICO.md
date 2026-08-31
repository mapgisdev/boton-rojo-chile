# 07 — Horizonte Temporal de Pronóstico: Evidencia de 3 vs 5 Días

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Componente:** Auditoría Forense del Horizonte de Pronóstico M0  
**Fecha:** 30 de agosto de 2026  
**Responsables:** Senior Geospatial Architect, Scientific Reproducibility Auditor, Fire Science Reviewer  

---

## 1. Planteamiento del Problema

Existe una aparente discrepancia en la literatura técnica y notas de prensa sobre el horizonte de pronóstico del Botón Rojo de CONAF:
- Diversos comunicados de prensa y documentos fundacionales históricos (2018–2020) hacen mención a un "pronóstico a 3 días".
- La documentación técnica formal de GEPRIF (2022–2023), los metadatos del ítem ArcGIS Online y los scripts operacionales en GEE y Python procesan **5 días** ($d_0, d_1, d_2, d_3, d_4$).

Este documento recopila la evidencia empírica, documental y de código para dictaminar la versión canónica que debe replicar la Línea Base M0.

---

## 2. Matriz de Evidencia Comparativa

| Fuente / Evidencia | Horizonte Declarado | Detalle / Cita Textual | Nivel de Evidencia |
|---|:---:|---|:---:|
| **Metadatos Oficiales ArcGIS Online** (`41ee3c691359437aa9df2a09d7f6124e`) | **5 días** | *"Su horizonte es de cinco días, con situación diaria y mapas de pronóstico publicados lunes, miércoles y viernes."* | **A** (Confirmado Institucional) |
| **Feature Services REST de CONAF** (`services5.arcgis.com/A1ELWse9bRAi2JiV/`) | **5 días** | Cada uno de los servicios (`TP`, `HR`, `HC`, `VV`, `PI`, `Boton_Rojo`) contiene exactamente 5 capas activas: `d0_AAAAMMDD_XX`, `d1_...`, `d2_...`, `d3_...`, `d4_...`. | **B** (Verificado Empíricamente) |
| **NASA DEVELOP Technical Paper (2022)** | **5 días** | Automatización en GEE para procesar corridas de 0 a 120 horas de pronóstico GFS ($5 \times 24 = 120\text{ h}$). | **A** (Confirmado Documental) |
| **Código Heredado GEE (`boton_rojo_gee.js`)** | **5 días** | `var N_DIAS = 5;` y filtrado `forecast_hours <= 120`. | **A** (Código Fuente Operacional) |
| **Código Heredado Python (`pipeline.py`, `nucleo.py`)** | **5 días** | `DIAS_PRONOSTICO = 5` en `nucleo.py` y cálculo de $d_0 \dots d_4$. | **A** (Código Fuente Operacional) |
| **Notas de Prensa Históricas (2018–2020)** | *3 días* | Versión inicial prototípica operada en Carto.com / ArcGIS Desktop antes de la migración a GEE. | Histórico superado |

---

## 3. Línea de Tiempo y Evolución del Sistema

```text
2018 (Lanzamiento inicial GEPRIF)
  │  - Prototipo inicial en Carto.com / ArcGIS Desktop.
  │  - Horizonte de pronóstico: 3 días (d0, d1, d2).
  │
2022 (Proyecto NASA DEVELOP / CONAF)
  │  - Migración y automatización en Google Earth Engine.
  │  - Extensión del horizonte a 120 horas (5 días).
  │
2023–2026 (Versión Operativa Vigente)
  │  - Operación continua en GEE y publicación en ArcGIS Online FeatureServer.
  │  - Estructura fija de 5 capas diarias (d0 a d4) por variable.
  ▼
LÍNEA BASE M0
  └─► Replicará con total fidelidad la versión operacional vigente a 5 días (d0..d4).
```

---

## 4. Decisión de Reconstrucción para M0

1. **Horizonte Oficial Congelado en M0:** Se fija estrictamente en **5 días** ($d_0, d_1, d_2, d_3, d_4$), cubriendo $120\ \mathrm{horas}$ de pronóstico meteorológico GFS.
2. **Tratamiento de la Versión Histórica de 3 días:** Se documenta como una fase previa superada del sistema institucional, no aplicable al paquete operacional recibido en `insumos/Boton_Rojo.zip`.
3. **Manejo de Latencia GFS:** En cada corrida diaria, la ventana se proyecta desde el día actual ($d_0$) hasta el cuarto día posterior ($d_4$), evaluando en cada uno de ellos los 5 pasos vespertinos ($14:00, 15:00, 16:00, 17:00, 18:00$).
