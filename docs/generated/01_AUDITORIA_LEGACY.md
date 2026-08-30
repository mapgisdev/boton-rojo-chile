# 01 — Auditoría Técnica y Científica del Sistema Legado Botón Rojo

Fecha de auditoría: 29 de agosto de 2026  
Módulo auditado: `work/legacy_boton_rojo/Boton_Rojo/`  
Responsables conceptuales: Fire Science Reviewer, Geospatial Architect, QA Engineer

---

## 1. Resumen Ejecutivo

El sistema **Botón Rojo** es una herramienta de pronóstico preventivo a 5 días desarrollada originalmente por GEPRIF/CONAF (2018, actualizada en 2023 sobre GEE y ArcGIS Online). Su función es identificar celdas territoriales donde coinciden condiciones críticas de ignición y velocidad de viento en la ventana vespertina (14:00–18:59 hora local).

Esta auditoría evaluó en profundidad la documentación institucional (`UIA_Metodologia_Boton_Rojo_CONAF.docx`), la réplica en Earth Engine (`boton_rojo_gee.js`), el núcleo algorítmico (`nucleo.py`), el pipeline desacoplado (`pipeline.py`), el cliente de cosecha (`conaf_api.py`) y la pila de despliegue (`publicar.py`, `compose.yaml`).

---

## 2. Desglose de la Cadena de Cálculo Legada

```text
 NOAA/GFS0P25 (0.25° ~ 28 km)
   │ (TMP 2m, RH 2m, u10, v10)
   ├─► HCFM = 0.297374 + 0.262·HR − 0.00982·T   (Regresión U. de Chile)
   ├─► Viento = √(u² + v²) · 3.6                (km/h a 10 m)
   ├─► Hillshade(SRTM 90m, az=313°, alt=60°)    (Reclass G: ≤123.5 -> 200, >123.5 -> 100)
   │
   ├─► Clave = ReclassC(HCFM) [2000..17000] + ReclassG [100|200] + ReclassA(T) [1..9]
   │
   ├─► PI = MATRIZ_PI[Clave]                    (Matriz de 288 celdas, 0..100 %)
   │
   ├─► Condición BR = (PI ≥ 70 %) ∧ (Viento ≥ 20 km/h)   (Binario RFW == 2)
   ├─► Acumulación: Horas = ∑ BR_h (1..5 pasos horarios en 14:00–18:59)
   ├─► Máscara combustible: ESA WorldCover 2021 (clases 10, 20, 30, 40, 90)
   └─► Estadística Zonal Comunal: SUM_br_ha, com_ha (combustible), proportion
```

---

## 3. Auditoría por Componente Científico y Técnico

### 3.1. Humedad del Combustible Fino Muerto (HCFM)
- **Fórmula:** $\mathrm{HCFM} = 0.297374 + 0.262 \cdot \mathrm{HR} - 0.00982 \cdot T$
- **Unidades:** $\mathrm{HR} \in [1, 100]\%$, $T \in [^\circ\mathrm{C}]$.
- **Origen:** Regresión lineal univariada de equilibrio desarrollada por la Universidad de Chile (documentada en NASA DEVELOP 2022).
- **Limitación científica:** Modelo puramente instantáneo. Carece de memoria temporal ($t-1, t-24\mathrm{h}$), no incorpora precipitación antecedente, balance de radiación solar ni déficit de presión de vapor (VPD). Trata igual un combustible tras 10 días de sequía que tras una lluvia intensa ocurrida la mañana previa.

### 3.2. Discretización y Tablas de Reclasificación (Reclass A a G)
- **Reclass A (Temperatura):** Corta en pasos de 5 °C desde $\le 0$ hasta 40 °C (clases 1 a 9).
  - *Defecto detectado:* $T > 40\ ^\circ\mathrm{C}$ no tiene clase asignada y se convierte en `NoData` / máscara. En olas de calor extremas (p.ej. 2017 y 2023 con $T > 41\ ^\circ\mathrm{C}$), el píxel se apaga justo en máximo peligro.
- **Reclass B (HCFM para visualización):** 10 clases (0–2, 2–4, ..., >25 %).
- **Reclass C (HCFM para indexación):** 16 clases de millares ($2.000, 3.000, \dots, 17.000$), equivalente a $1.000 \cdot \lceil\mathrm{HCFM}\rceil$ acotado en $[2.000, 17.000]$.
  - *Defecto detectado:* $\mathrm{HCFM} > 30\%$ se enmascara como `NoData`.
- **Reclass D (Probabilidad de ignición):** Deciles 1..10 (10 %, 20 %, ..., 100 %).
- **Reclass E (Viento para visualización):** 8 clases (Calmo, 3–5, 5–10, 10–15, 15–20, 20–25, 25–30, >30 km/h).
- **Reclass F (Viento binario):** $< 20\ \mathrm{km/h} \to 0$, $\ge 20\ \mathrm{km/h} \to 1$.
- **Reclass G (Sombreado / Exposición):** Hillshade sobre SRTM 90 m con azimut 313° y elevación solar 60°.
  - $\text{Hillshade} \le 123.5 \to 200$ (Sombreado)
  - $\text{Hillshade} > 123.5 \to 100$ (Expuesto)

### 3.3. Matriz de Probabilidad de Ignición (PI)
- **Estructura:** 288 celdas ($16\ \text{HCFM} \times 2\ \text{Sombreado} \times 9\ \text{Temperatura}$).
- **Linaje:** Tabla de *Probability of Ignition* del NWCG / Rothermel / BehavePlus (`ignite.cpp`, Schroeder 1969).
- **Brecha institucional fundamental:** CONAF no publica su matriz de 288 valores. Según NASA DEVELOP (2022), CONAF calibró empíricamente sus coeficientes usando la temporada chilena 2016–2017 como referencia.
- **Efecto de la reconstrucción Rothermel:** La matriz teórica de Rothermel es conservadora: requiere $\mathrm{HCFM} \le 4\%$ ($\mathrm{HR} \le 15.2\%$ a 30 °C) para alcanzar $\mathrm{PI} \ge 70\%$. Si CONAF activa con $\mathrm{HR} \sim 20\text{--}25\%$, su matriz institucional es sustancialmente más permisiva.

### 3.4. Viento y Umbral de Activación
- **Cálculo:** Módulo euclidiano $\sqrt{u^2 + v^2} \times 3.6$ a partir de $u_{10}, v_{10}$ de GFS 0.25°.
- **Regla:** $(\mathrm{PI} \ge 70\%) \land (\mathrm{Viento} \ge 20\ \mathrm{km/h})$.

### 3.5. Resolución Analítica Real vs Resolución Publicada
- **Insumo meteorológico:** GFS 0.25° ($\approx 27.8\ \mathrm{km}$ en el ecuador, $\approx 22\text{--}25\ \mathrm{km}$ en Chile).
- **Resolución declarada (`ESCALA_INDICE`):** $2.000\ \mathrm{m}$ ($4.000.000\ \mathrm{m}^2$ en EPSG:3857).
- **Resolución zonal (`ESCALA_ZONAL`):** $500\ \mathrm{m}$ ($25\ \mathrm{ha}$).
- **Veredicto:** El remuestreo de $25\ \mathrm{km} \to 2\ \mathrm{km}$ en el legado es **interpolación geométrica/bilineal pura**, no downscaling físico. No añade resolución micrometeorológica ni resuelve vientos de quebrada (Puelche, Raco, Terral).

### 3.6. Resampling en GEE y Defecto de Interpolación Categórica
- En `boton_rojo_gee.js` línea 192:
  ```javascript
  return ee.Image.cat([t.rename('TP'), hr.rename('HR'), hcfm, viento, pi,
                       rfw.eq(2).rename('BR')])
           .resample('bilinear')
  ```
- **Hallazgo crítico:** Aplicar `.resample('bilinear')` a un stack que incluye bandas binarias y categóricas (`BR`, `RFW`, `PI`) produce valores espurios no enteros en los límites de activación. El resampling debe restringirse a campos meteorológicos continuos ($T, \mathrm{HR}, V$) y procesar la lógica booleana posteriormente.

### 3.7. Tratamiento Horario y Husos UTC
- En `boton_rojo_gee.js` línea 96:
  ```javascript
  var DESFASE_UTC = -4; // Hardcoded
  ```
- **Hallazgo:** Chile continental alterna entre `UTC-3` (horario de verano: primer sábado de septiembre al primer sábado de abril) y `UTC-4` (horario estándar: primer sábado de abril al primer sábado de septiembre). Un desfase estático de -4 genera un desfase de 1 hora durante 7 meses del año (precisamente en temporada alta de incendios de verano), evaluando 15:00–19:59 en lugar de 14:00–18:59.

### 3.8. Salida Comunal y Definición de `com_ha`
- **Hallazgo confirmado:** En la tabla comunal oficial, el campo `com_ha` **NO es la superficie total de la comuna**, sino su **superficie combustible** calculada como la suma de píxeles de $500 \times 500\ \mathrm{m}$ ($25\ \mathrm{ha}$) sobre clases ESA WorldCover (10, 20, 30, 40, 90).
- `proportion` es exactamente $\frac{\mathrm{SUM\_br\_ha}}{\mathrm{com\_ha}}$.

### 3.9. Dependencias de la Pila de Despliegue Legada
- La carpeta `despliegue/` propone una pila compleja para operar el índice fuera de GEE:
  - PostGIS + pgstac + TiTiler + Martin + pygeoapi + Grafana + systemd.
- **Veredicto para BR-HR:** Innecesariamente pesada para el MVP. Introduce alta deuda de infraestructura. La arquitectura BR-HR sustituye esta carga con:
  - Google Earth Engine REST + Railway API ligera + Cloudflare R2 (PMTiles + Parquet + JSON) + GeoLibre.

---

## 4. Especificación del Baseline Congelado (M0 — BR-CONAF)

Para garantizar regresión cero y comparabilidad histórica, el baseline M0 se congelará bajo las siguientes reglas:

1. **Mapeo exacto de fórmulas:** Mantener regresión HCFM U. de Chile, cálculo de viento $\sqrt{u^2+v^2} \times 3.6$, Hillshade SRTM 90 m (azimut 313°, altitud 60°), y tablas Reclass A-G.
2. **Corrección técnica no metodológica:**
   - Corrección dinámica de zona horaria `America/Santiago` (UTC-3 / UTC-4).
   - Eliminación de bilinear sobre capas discretas (resamplear solo inputs continuos antes de clasificar).
   - Manejo seguro de bordes ($T > 40\ ^\circ\mathrm{C}$ asignado a clase 9 en vez de NoData; $\mathrm{HCFM} > 30\%$ a clase 17000; Viento $\ge 0$).
3. **Reproducibilidad dual:** Implementación idéntica en Python puro (`src/baseline/conaf_core.py`) y en GEE (`src/gee/baseline/`).
4. **Golden Fixtures:** Conjunto de vectores de prueba unitarios con casos extremos y verificación cruzada Python $\leftrightarrow$ GEE.
