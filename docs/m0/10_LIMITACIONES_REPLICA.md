# 10 — Limitaciones Metodológicas y Científicas del Modelo M0

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Componente:** Auditoría Crítica de Limitaciones del Baseline M0  
**Fecha:** 30 de agosto de 2026  
**Responsables:** Fire Science Reviewer, Scientific Reproducibility Auditor, Senior Geospatial Architect  

---

## 1. Resumen de Limitaciones Estructurales

La auditoría forense del Botón Rojo original (CONAF/GEPRIF) identifica seis limitaciones científicas fundamentales. Estas limitaciones no deben "corregirse" dentro de M0 —pues desvirtuarían su rol como réplica de línea base—, sino que constituyen la justificación técnica que motiva el desarrollo de **BR-HR**:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       LIMITACIONES ESTRUCTURALES DE M0                      │
├─────────────────────────────────────────────────────────────────────────────┤
│ 1. Resolución Meteorológica Efectiva: ~25 km nativa (suavizado a 2 km)      │
│ 2. Ausencia de Memoria Temporal en HCFM (modelo instantáneo sin sequía/lluvia)│
│ 3. Máscara de Combustible Binaria (sin carga, tipo de combustible ni curado)│
│ 4. Ignorancia del Factor Antrópico (vulnerabilidad e interfaz urbano-forestal)│
│ 5. Discretización Rígida y Agregación Comunal (pérdida de heterogeneidad)   │
│ 6. Defectos de Borde en Reclasificaciones (apagado en T > 40 °C)            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Análisis Detallado de Cada Limitación

### 2.1. Resolución Efectiva vs. Viento Local de Terreno
- El modelo meteorológico numérico base es NOAA GFS a $0.25^\circ$ ($\approx 25\ \mathrm{km}$).
- La publicación sobre una malla de $2\ \mathrm{km}$ en ArcGIS Online es una operación de interpolación geométrica bilineal, **no un downscaling micro-meteorológico dinámico**.
- **Impacto en Incendios:** No resuelve fenómenos orográficos críticos de Chile, como el viento Puelche (viento catabático cálido y seco de cordillera en Biobío y Ñuble), el Raco en la cuenca de Santiago, el Terral en Coquimbo, ni las brisas de ladera y cañón en valles intermedios.

### 2.2. Modelo de Humedad sin Memoria Temporal ni Precipitación Antecedente
- La fórmula $\mathrm{HCFM} = 0.297374 + 0.262 \cdot \mathrm{HR} - 0.00982 \cdot T$ calcula la humedad de equilibrio instantáneo.
- **Impacto en Incendios:** No incorpora precipitación previa ($t-24\mathrm{h}, t-72\mathrm{h}$), déficit de presión de vapor (VPD) acumulado, radiación solar histórica ni balance hídrico del suelo. Trata idénticamente un matorral sometido a 15 días continuos de ola de calor y sequía que uno que recibió una precipitación torrencial 4 horas antes si $T$ y $\mathrm{HR}$ coinciden en la tarde.

### 2.3. Máscara de Combustible Binaria y Estática
- M0 utiliza una máscara estática booleana (clases 10, 20, 30, 40, 90 de ESA WorldCover 2021).
- **Impacto en Incendios:** Trata con el mismo peso una plantación densa de pino/eucalipto que un pastizal ralo o un cultivo de regadío. No considera el estado de curado del pastizal (*curing fraction*), la carga de combustible ($\mathrm{ton/ha}$), la continuidad vertical ni los cambios intra-anuales de fenología.

### 2.4. Inexistencia de Factores de Ignición Antrópica y Exposición
- En Chile, más del $99.7\%$ de los incendios forestales son de origen antrópico (accidental o intencional).
- M0 modela exclusivamente el peligro físico de propagación condicional, ignorando la densidad poblacional, la red vial, las líneas de transmisión eléctrica, las faenas agrícolas/forestales y la interfaz urbano-forestal (WUI).

### 2.5. Agregación Comunal y Falacia Ecológica
- Al condensar la salida a nivel comunal (`SUM_br_ha`, `proportion`), comunas de gran extensión territorial (p. ej. San José de Maipo, Panguipulli, Lonquimay) diluyen focos hiper-críticos de riesgo local, mientras que comunas periurbanas pequeñas pueden mostrar proporciones alarmantes por unas pocas hectáreas activas.

### 2.6. Defectos de Borde en las Tablas Reclass A, C y F
- **Reclass A:** No define clase para $T > 40\ ^\circ\mathrm{C}$, enviando el píxel a `NoData`. Esto produce la paradoja de apagar el Botón Rojo en el momento de mayor severidad térmica histórica (p. ej. olas de calor extremas de 2017 y 2023 con temperaturas de $41\text{--}42\ ^\circ\mathrm{C}$).
- **Reclass C:** No define clase para $\mathrm{HCFM} > 30\%$, convirtiéndolo en `NoData`.
- **Reclass F:** Rango original inicia en $0.0001\ \mathrm{km/h}$, dejando celdas con viento estrictamente nulo sin clasificar.
