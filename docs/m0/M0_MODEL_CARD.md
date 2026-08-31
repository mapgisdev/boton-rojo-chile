# Model Card — Línea Base M0 (Botón Rojo Original CONAF)

**Identificador del Modelo:** `BR-M0-BASELINE`  
**Versión Congelada:** `1.0.0`  
**Fecha de Publicación:** 30 de agosto de 2026  
**Institución Creadora:** CONAF / GEPRIF (Departamento de Desarrollo e Investigación)  
**Entidades de Reconstrucción y Auditoría:** Antigravity AI, Senior Geospatial Architect, Fire Science Reviewer  
**Licencia de Datos:** Uso público con cita obligatoria a CONAF / GEPRIF  

---

## 1. Descripción y Propósito

El modelo **M0** es la reconstrucción exacta, independiente y reproducible de la metodología original del **Índice Botón Rojo** desarrollado por CONAF para el pronóstico preventivo de condiciones extremas de ignición y propagación de incendios forestales en Chile continental.

### Uso Previsto
- Actuar como **Línea Base Científica Congelada (Control Experimental)** contra la cual se medirá el valor agregado cuantitativo, la ganancia en resolución espacial y la destreza predictiva del nuevo sistema **BR-HR**.
- Generar pronósticos retrospectivos (*hindcasts*) y operacionales utilizando idénticas variables, tablas de reclasificación, matriz de probabilidad de ignición, ventana temporal y agregación comunal que el sistema oficial.

### Usos No Previstos
- No debe utilizarse como simulador de propagación física de frentes de llama ni como modelo de comportamiento del fuego en tiempo real.
- No reemplaza la toma de decisiones tácticas de despacho y combate de incendios.
- No debe modificarse internamente con innovaciones de BR-HR (como mallas H3, machine learning o modelos continuos).

---

## 2. Especificación Técnica de Entradas y Salidas

### Insumos del Sistema
1. **Meteorología:** `NOAA/GFS0P25` (Temperatura a 2 m, Humedad Relativa a 2 m, Viento $u_{10}$ y $v_{10}$ a 10 m).
2. **Topografía:** `CGIAR/SRTM90_V4` (DEM 90 m, cálculo de *hillshade* con azimut 313° y elevación 60°).
3. **Combustible:** `ESA/WorldCover/v200` (Año 2021; clases 10, 20, 30, 40, 90).
4. **Límites:** División Político-Administrativa de Chile 2023 (SUBDERE/IGM/INE).

### Salida Comunal Oficial
- `date`: Fecha de pronóstico ($d_0, d_1, d_2, d_3, d_4$).
- `com_id`: Código Único Territorial (CUT) de la comuna.
- `horas`: Número de horas críticas simultáneas ($1 \dots 5$) en la ventana vespertina (14:00–18:59).
- `com_ha`: Superficie combustible de la comuna (hectáreas).
- `SUM_br_ha`: Superficie activa en condición BR (hectáreas).
- `proportion`: Proporción de superficie combustible afectada ($\mathrm{SUM\_br\_ha} / \mathrm{com\_ha}$).

---

## 3. Cadena de Transformación Matemática

$$\mathrm{HCFM} = 0.297374 + 0.262 \cdot \mathrm{HR} - 0.00982 \cdot T$$

$$V = \sqrt{u_{10}^2 + v_{10}^2} \times 3.6 \quad [\mathrm{km/h}]$$

$$\mathrm{ReclassG}(\mathrm{Hillshade}) = \begin{cases} 200 & \text{si } \mathrm{Hillshade} \le 123.5 \\ 100 & \text{si } \mathrm{Hillshade} > 123.5 \end{cases}$$

$$\mathrm{Clave} = \mathrm{ReclassC}(\mathrm{HCFM}) + \mathrm{ReclassG}(\mathrm{Hillshade}) + \mathrm{ReclassA}(T)$$

$$\mathrm{PI} = \mathrm{MATRIZ\_PI}[\mathrm{Clave}] \quad [0.0 \dots 100.0\%]$$

$$\mathrm{BR}_t = (\mathrm{PI}_t \ge 70.0) \land (V_t \ge 20.0)$$

$$\mathrm{HorasBR} = \sum_{t=14}^{18} \mathrm{BR}_t \quad \in \{0, 1, 2, 3, 4, 5\}$$

$$\mathrm{SUM\_br\_ha}(c, d, h) = \text{Área en ha de celdas combustibles de la comuna } c \text{ con } \mathrm{HorasBR} = h$$

---

## 4. Clasificación de Evidencia de Componentes

- **Confirmados [A]:** Meteorología GFS, ventana 14–18:59, horizonte 5 días, fórmula HCFM, fórmula viento, parámetros Hillshade, tablas Reclass A a G, máscara combustible WorldCover, umbrales $PI \ge 70$ y $V \ge 20$.
- **Verificados Empíricamente [B]:** Malla de cálculo a 2 km ($4.000.000\ \mathrm{m}^2$), contabilidad zonal a 500 m ($25\ \mathrm{ha}$), significado de `com_ha` como superficie combustible y no total, fórmula de `proportion`.
- **Reconstruidos [C]:** Coeficientes de la Matriz PI de 288 celdas (derivados de Rothermel/BehavePlus; CONAF la calibró internamente con la temporada 2016-2017).

---

## 5. Control de Versiones y Congelamiento

- **Estado:** `M0_FROZEN = TRUE`
- **Versión:** `1.0.0`
- **Política de Inmutabilidad:** Queda estrictamente prohibido alterar cualquier fórmula, umbral o paso de M0 en fases posteriores de evaluación o comparación con BR-HR. Cualquier ajuste metodológico futuro deberá publicarse bajo una nueva versión (`1.1.0` o `2.0.0`) y registrarse en `docs/m0/DECISION_LOG.md`.
