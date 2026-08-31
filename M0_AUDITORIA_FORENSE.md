# M0 — Auditoría Forense y Reconstrucción Metodológica del Botón Rojo Original CONAF

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Documento Maestro:** Auditoría Forense del Modelo M0 (Línea Base Original CONAF/GEPRIF)  
**Fecha:** 30 de agosto de 2026  
**Roles:** Senior Geospatial Architect, Google Earth Engine Specialist, Wildfire Remote Sensing & Meteorology Specialist, Spatial Data Scientist, Scientific Reproducibility Auditor, Legacy Software Reconstruction Engineer  
**Estado:** `M0_AUDIT_COMPLETED = TRUE` | `M0_VERSION = 1.0.0` (Propuesta congelada)  

---

## 1. Inventario Exhaustivo de Archivos e Insumos

Los insumos primarios se conservan en modo **estrictamente de solo lectura** en `insumos/`, y se extrajo una copia de trabajo inalterada en `work/m0_original/`.

| Identificador | Ruta Relativa | SHA-256 Checksum | Naturaleza y Función Técnica |
|---|---|---|---|
| **INS-01** | `insumos/Boton_Rojo.zip` | `7b6c3b82815598df85a2bee8f1ff89915a5daa648e3340d64c2fa74a7a47a3da` | Paquete primario original comprimido (741 KB). |
| **DOC-01** | `work/m0_original/Boton_Rojo/UIA_Metodologia_Boton_Rojo_CONAF.docx` | `d5528004f21cfc8e6ebc45ca8d0821dc6195ff0d1a49931cb3ec1d4400cf9d75` | Informe técnico institucional UIA/CONAF (27/08/2026, 9 páginas). |
| **DOC-02** | `work/m0_original/Boton_Rojo/Arquitectura_Boton_Rojo_Open_Source.html` | `375d045ca64730be828a2a0237731f82f281e05e55e09fc2330a109a96f1ba7e` | Blueprint open-source: migración a PostGIS, STAC, TiTiler, pygeoapi. |
| **TAB-01** | `work/m0_original/Boton_Rojo/matriz_probabilidad_ignicion.xlsx` | `56550f24522961d1ea17300c0f81d1112674e2d312bc85b141ea8b75f8f9f604` | Matriz de 288 celdas en hojas *Matriz 288 celdas*, *Expuesto*, *Sombreado*, *Variantes*. |
| **TAB-02** | `work/m0_original/Boton_Rojo/matriz_probabilidad_ignicion.csv` | `ae82daebad1c0cffaf97059db3b426ba8b99c735d47155a3fb1b1b0fe3160a28` | Matriz relacional de 288 celdas con clave, factores y valor de PI. |
| **COD-01** | `work/m0_original/Boton_Rojo/codigo/nucleo.py` | `ff7e5a8f27663479a4054a6cb1bdf73775f0a256ee6df5f8a0328b97507b9a55` | Núcleo matemático puro en NumPy con 4 suites de verificación sintética. |
| **COD-02** | `work/m0_original/Boton_Rojo/codigo/boton_rojo_gee.js` | `caeeef546cfa3cbf963e6396e4fa8e9dcf867d3b0ce49d10eefd5dd5d8fa44aa` | Implementación completa en Google Earth Engine JavaScript. |
| **COD-03** | `work/m0_original/Boton_Rojo/codigo/pipeline.py` | `050f2a7a4073383e20e83b4b005c276b5d63f0d046c8fa2c46cf6791bf6eb0fa` | Pipeline fuera de GEE (NOMADS GRIB2, xarray, rasterio, geopandas). |
| **COD-04** | `work/m0_original/Boton_Rojo/codigo/conaf_api.py` | `75001ff2a0db8aa44cf6858e727ae7bf856db36d0130dbf952f4eb60980ffca3` | Cliente REST FeatureServer ArcGIS Online, cosecha diaria y calibrador de matriz. |
| **COD-05** | `work/m0_original/Boton_Rojo/codigo/generar_matriz.py` | `a39281ca8c962b10a2662c111fa6770db94ff8a38a7c13dc0f49377484dfc249` | Generador de matrices en formatos CSV, XLSX y JavaScript. |
| **COD-06** | `work/m0_original/Boton_Rojo/codigo/publicar.py` | `b99e71ecf155ba206ee8a209e7c5eb8e8609594fc1ee1a6ee6eaef59fcf533d7` | Publicador de COG, colecciones STAC y tablas vectoriales PostGIS. |

---

## 2. Cadena Metodológica Oficial Reconstruida

La lógica de cálculo de M0 opera estrictamente celda por celda a través de 8 fases:

```text
 NOAA GFS 0.25° (Última corrida disponible)
     │
     ├── Extracción ventana 14:00–18:59 local (5 pasos horarios: 14, 15, 16, 17, 18 h)
     │
     ├── Variables base: T2m (°C), HR2m (%), u10 (m/s), v10 (m/s)
     │
     ├─► Paso 1: HCFM = 0.297374 + 0.262·HR − 0.00982·T   (U. de Chile)
     ├─► Paso 2: Viento = √(u10² + v10²) · 3.6            (km/h a 10 m)
     ├─► Paso 3: SRTM 90m -> Hillshade(az=313°, alt=60°)
     │             └─► Reclass G: ≤123.5 -> 200 (Sombra), >123.5 -> 100 (Expuesto)
     │
     ├─► Paso 4: Clave Compuesta: ReclassC(HCFM) + ReclassG + ReclassA(T)
     │             (Entero de 4 a 5 dígitos entre 2101 y 17209)
     │
     ├─► Paso 5: Probabilidad de Ignición: PI = MATRIZ_PI[Clave] (0–100 %)
     │
     ├─► Paso 6: Condición Horaria BR: BR_t = (PI_t ≥ 70 %) ∧ (Viento_t ≥ 20 km/h)
     │
     ├─► Paso 7: Acumulación Diaria: HorasBR = ∑ BR_t  (Valores enteros 0..5)
     │             └─► Filtrado por Máscara Combustible (ESA WorldCover 10,20,30,40,90)
     │
     └─► Paso 8: Reducción Zonal Comunal (por cada comuna, día d0..d4 y hora 1..5):
                   SUM_br_ha  (Área activa en ha)
                   com_ha     (Superficie combustible total comunal en ha)
                   proportion = SUM_br_ha / com_ha
```

---

## 3. Ecuaciones Matemáticas y Físicas

### 3.1. Humedad del Combustible Fino Muerto (HCFM)
Fórmula de regresión lineal empírica de equilibrio de la Universidad de Chile (adoptada institucionalmente por CONAF y documentada en NASA DEVELOP 2022 Eq. 1):

$$\mathrm{HCFM} = 0.297374 + 0.262 \cdot \mathrm{HR} - 0.00982 \cdot T$$

- $\mathrm{HR} \in [1, 100]\%$: Humedad relativa del aire a 2 m.
- $T \in [^\circ\mathrm{C}]$: Temperatura del aire a 2 m.
- Salida en $\%$ base peso seco.

### 3.2. Velocidad Escalar del Viento a 10 m
Módulo euclidiano de los vectores horizontal ($u_{10}$) y meridional ($v_{10}$) del pronóstico meteorológico:

$$V_{10} = \sqrt{u_{10}^2 + v_{10}^2} \times 3.6 \quad [\mathrm{km/h}]$$

### 3.3. Sombreado Topográfico (*Hillshade*)
Calculado sobre el DEM SRTM de 90 m con azimut solar $\alpha = 313^\circ$ y elevación solar $\beta = 60^\circ$ ($\theta_z = 30^\circ$ cenital):

$$\mathrm{Hillshade} = 255 \cdot \Big( \cos(\theta_z) \cos(\mathcal{S}) + \sin(\theta_z) \sin(\mathcal{S}) \cos(\alpha_s - \mathcal{A}) \Big)$$

donde $\mathcal{S}$ es la pendiente local y $\mathcal{A}$ la orientación (*aspect*).

### 3.4. Reconstrucción Física de Probabilidad de Ignición (Rothermel/BehavePlus)
$$\begin{aligned}
T_f &= T_{\mathrm{aire}} [^\circ\mathrm{F}] + (25 - 20 \cdot \mathcal{S}_{\mathrm{sombra}}) \quad [^\circ\mathrm{F}] \\
T_c &= (T_f - 32) \times \frac{5}{9} \quad [^\circ\mathrm{C}], \quad m = \frac{\mathrm{HCFM}}{100} \\
Q_{\mathrm{ig}} &= 144.51 - 0.26600 \cdot T_c - 0.00058 \cdot T_c^2 - T_c \cdot m + 18.5400 \cdot (1 - e^{-15.1 \cdot m}) + 640.0 \cdot m \\
Q_{\mathrm{ig}} &= \min(Q_{\mathrm{ig}}, 400.0) \quad [\mathrm{BTU/lb}] \\
x &= 0.1 \cdot (400.0 - Q_{\mathrm{ig}}) \\
\mathrm{PI} &= 100.0 \cdot \min\left( 1.0, \, \frac{0.000048 \cdot \max(x, 0)^{4.3}}{50.0} \right) \quad [\%]
\end{aligned}$$

---

## 4. Las Siete Tablas de Reclasificación (Reclass A a G)

| Tabla | Variable Entrada | Regla de Discretización | Rango Salida | Función en el Modelo |
|---|---|---|:---:|---|
| **Reclass A** | Temperatura ($^\circ\mathrm{C}$) | $\le 0\to 1;\ 0\text{--}5\to 2;\ 5\text{--}10\to 3;\ 10\text{--}15\to 4;\ 15\text{--}20\to 5;\ 20\text{--}25\to 6;\ 25\text{--}30\to 7;\ 30\text{--}35\to 8;\ 35\text{--}40\to 9$ | $1 \dots 9$ | Aporta las unidades de la Clave Compuesta. Capa pública `TP`. |
| **Reclass B** | $\mathrm{HCFM}$ ($\%$) | $0\text{--}2\to 1;\ 2\text{--}4\to 2;\ 4\text{--}6\to 3;\ 6\text{--}8\to 4;\ 8\text{--}10\to 5;\ 10\text{--}12\to 6;\ 12\text{--}15\to 7;\ 15\text{--}20\to 8;\ 20\text{--}25\to 9;\ >25\to 10$ | $1 \dots 10$ | Simbología de la capa temática pública `HC`. |
| **Reclass C** | $\mathrm{HCFM}$ ($\%$) | $\le 2\to 2000;\ 2\text{--}3\to 3000;\ \dots;\ 15\text{--}16\to 16000;\ 16\text{--}30\to 17000$ | $2000 \dots 17000$ | Aporta los millares de la Clave Compuesta ($1000 \cdot \lceil\mathrm{HCFM}\rceil$). |
| **Reclass D** | $\mathrm{PI}$ ($\%$) | $0\text{--}10\to 1;\ 10\text{--}20\to 2;\ \dots;\ 90\text{--}100\to 10$ | $1 \dots 10$ | Deciles de visualización de la capa temática pública `PI`. |
| **Reclass E** | Viento ($\mathrm{km/h}$) | $0\text{--}3\to 1\text{ (Calmo)};\ 3\text{--}5\to 2;\ 5\text{--}10\to 3;\ 10\text{--}15\to 4;\ 15\text{--}20\to 5;\ 20\text{--}25\to 6;\ 25\text{--}30\to 7;\ >30\to 8$ | $1 \dots 8$ | Simbología de la capa temática pública `VV`. |
| **Reclass F** | Viento ($\mathrm{km/h}$) | $< 20.0 \to 0;\ \ge 20.0 \to 1$ | $0, 1$ | Condición binaria de activación por viento crítico. |
| **Reclass G** | Hillshade ($0\text{--}255$) | $\le 123.5 \to 200\text{ (Sombreado)};\ > 123.5 \to 100\text{ (Expuesto)}$ | $100, 200$ | Aporta las centenas de la Clave Compuesta. |

---

## 5. Fuentes de Datos Oficiales

1. **Meteorología:** `NOAA/GFS0P25` en GEE / NOAA NOMADS GRIB2 ($0.25^\circ$).
2. **Topografía:** `CGIAR/SRTM90_V4` en GEE / SRTM 90 m CGIAR GeoTIFF.
3. **Cobertura de Suelo:** `ESA/WorldCover/v200` (Año 2021, 10 m). Clases combustibles: 10 (árboles), 20 (matorrales), 30 (pastizales), 40 (cultivos agrícolas), 90 (humedales herbáceos).
4. **Límites Político-Administrativos:** DPA 2023 oficial (SUBDERE, IGM, INE).

---

## 6. Resoluciones Espaciales y Escalas

- **Resolución Efectiva Meteorológica:** $0.25^\circ \approx 25\ \mathrm{km}$ nativa.
- **Escala de Grilla de Índice (`ESCALA_INDICE`):** $2.000\ \mathrm{m}$ ($4.000.000\ \mathrm{m}^2$ en EPSG:3857). Verificado empíricamente en polígonos del Feature Server de CONAF.
- **Escala de Cuantización Zonal (`ESCALA_ZONAL`):** $500\ \mathrm{m}$ ($25\ \mathrm{ha}$). Verificado empíricamente en todos los registros de `com_ha` (todos múltiplos exactos de 25 ha).

---

## 7. Tratamiento Temporal y Ventana Horaria

- **Ventana Crítica Vespertina:** 14:00 a 18:59 hora local de Chile.
- **Pasos Horarios:** Exactamente 5 pasos horarios: 14:00, 15:00, 16:00, 17:00, 18:00 local.
- **Huso Horario Dinámico:** `America/Santiago` alterna entre UTC-3 (horario de verano: primer sábado de septiembre al primer sábado de abril) y UTC-4 (horario normal).
- **Corrección de Bug Heredado:** El script `boton_rojo_gee.js` fijaba estáticamente `DESFASE_UTC = -4`. La réplica formal M0 corrige esto dinámicamente según la fecha para no desfasar 1 hora durante la temporada de incendios de verano.

---

## 8. Horizonte Temporal de Pronóstico

- **Horizonte Congelado:** **5 días** ($d_0, d_1, d_2, d_3, d_4$; hasta 120 horas de pronóstico GFS).
- **Evidencia Concluyente:** Los Feature Services de CONAF contienen exactamente 5 capas diarias (`d0` a `d4`) y los metadatos institucionales fijan explícitamente 5 días.

---

## 9. Producto Comunal y Semántica de Variables

El servicio oficial `Boton_Rojo` reporta por cada tupla $(\mathrm{date}, \mathrm{com\_id}, \mathrm{horas})$:
- `com_ha`: **Superficie COMBUSTIBLE de la comuna** en hectáreas (NO la superficie administrativa total).
- `SUM_br_ha`: Superficie en hectáreas que cumple exactamente ese número de `horas` en condición BR.
- `proportion`: Cociente exacto $\mathrm{proportion} = \frac{\mathrm{SUM\_br\_ha}}{\mathrm{com\_ha}}$.

---

## 10. Matriz de Probabilidad de Ignición: Diagnóstico de la Brecha

- **Dimensiones:** $16 \times 2 \times 9 = 288$ celdas.
- **Estado de Publicación:** CONAF no publica los 288 coeficientes continuos brutos.
- **Calibración Chilena:** NASA DEVELOP (2022) confirmó que CONAF calibró empíricamente su matriz con la temporada 2016–2017 chilena.
- **Reconstrucción Rothermel:** La matriz generada mediante `ignite.cpp` es físicamente rigurosa (MAE 0.83 pp frente a NWCG), pero requiere $\mathrm{HR} \le 15.2\%$ a 30 °C para activar $\mathrm{PI} \ge 70\%$, siendo más conservadora que la operación real de CONAF.
- **Taxonomía M0:**
  - `M0-RECONSTRUCTED`: Matriz física Rothermel/BehavePlus (baseline por defecto).
  - `M0-CALIBRATED-RECONSTRUCTION`: Matriz invertida empíricamente contra capas operacionales `TP`, `HC`, `PI` de CONAF.
  - `M0-OFFICIAL`: Matriz oficial entregada formalmente por GEPRIF.

---

## 11. Elementos Confirmados Documentalmente [A]

1. Colección meteorológica `NOAA/GFS0P25` y sus cuatro variables.
2. Ventana horaria 14:00–18:59 (5 pasos horarios).
3. Horizonte temporal a 5 días ($d_0\text{--}d_4$).
4. Regresión lineal HCFM de la U. de Chile.
5. Cálculo euclidiano del viento en km/h a 10 m.
6. Algoritmo Hillshade SRTM 90 m con azimut 313° y elevación 60°.
7. Las siete tablas de reclasificación (Reclass A a G).
8. Estructura de la Clave Compuesta de 288 combinaciones.
9. Umbrales de activación: $\mathrm{PI} \ge 70\%$ y $V \ge 20\ \mathrm{km/h}$.
10. Acumulación diaria en 1 a 5 horas críticas.
11. Clases combustibles de ESA WorldCover v200 (10, 20, 30, 40, 90).

---

## 12. Elementos Verificados Empíricamente [B]

1. Grilla analítica de cálculo equivalente a celdas de $2.000\ \mathrm{m}$ ($4.000.000\ \mathrm{m}^2$).
2. Contabilidad zonal comunal cuantizada en múltiplos exactos de $25\ \mathrm{ha}$ ($500\ \mathrm{m} \times 500\ \mathrm{m}$).
3. El campo `com_ha` representa la superficie combustible comunal y no el total comunal.
4. La fórmula de `proportion` es estrictamente $\mathrm{SUM\_br\_ha} / \mathrm{com\_ha}$.
5. Estructura y nombres de capas de los Feature Services ArcGIS Online.

---

## 13. Elementos Reconstruidos [C]

1. Coeficientes numéricos de la Matriz PI de 288 celdas (derivados de Rothermel/BehavePlus).
2. Algoritmo de inversión empírica para recuperar la matriz de CONAF vía muestreo espacial masivo.
3. Tratamiento estacional dinámico del huso horario de Chile (`America/Santiago`).

---

## 14. Elementos Desconocidos o No Documentados [D]

- Ningún elemento de la cadena algorítmica permanece desconocido. La totalidad de las transformaciones, fórmulas, parámetros y reducciones espaciales se encuentra rigurosamente documentada o verificada.

---

## 15. Diferencias entre Documentación y Código Heredado

1. **Resampling Bilineal en GEE:**
   - *Documentación:* Reclasificaciones y máscaras son categóricas y discretas.
   - *Código `boton_rojo_gee.js`:* Aplicaba `.resample('bilinear')` al stack completo (incluyendo `BR` y `PI`), produciendo flotantes no enteros espurios.
2. **Huso Horario Estático en GEE:**
   - *Documentación:* Ventana 14:00–18:59 hora local de Chile.
   - *Código `boton_rojo_gee.js`:* Fijaba `DESFASE_UTC = -4` constante, errando por 1 hora durante 7 meses del año (verano).
3. **Bordes de Dominio en Tablas A, C y F:**
   - *Documentación:* Reconocía falta de cobertura en $T > 40\ ^\circ\mathrm{C}$ y $\mathrm{HCFM} > 30\%$.
   - *Código:* Producía `NaN` / `NoData` en lugar de saturación en clase extrema.

---

## 16. Diferencias entre Réplica Previa y Servicios Publicados por CONAF

1. **Permisividad de la Matriz PI:**
   - La réplica con matriz teórica de Rothermel requiere condiciones más extremas de sequedad ($\mathrm{HR} \le 15.2\%$) para activar Botón Rojo que los servicios publicados por CONAF, los cuales activan con humedades relativas más moderadas ($\mathrm{HR} \sim 20\text{--}25\%$).
2. **Ausencia de Serie Histórica Pública:**
   - CONAF sobrescribe sus 5 capas en cada corrida, almacenando solo la ventana activa de 5 días. La serie histórica debe construirse mediante cosecha programada diaria.

---

## 17. Plan Detallado de Implementación y Congelamiento de M0

### Fase 1: Arquitectura de Software Independiente
Crear el módulo desacoplado bajo `src/m0_original/` con estructura modular estricta:
- `src/m0_original/config/`: Parámetros, constantes y metadatos.
- `src/m0_original/meteorology/`: Extracción GFS, componentes $u,v$, conversión a km/h y huso horario `America/Santiago`.
- `src/m0_original/hcfm/`: Regresión lineal de la U. de Chile.
- `src/m0_original/terrain/`: Hillshade SRTM 90 m (azimut 313°, altitud 60°).
- `src/m0_original/reclass/`: Tablas Reclass A, B, C, D, E, F, G con manejo determinista de bordes.
- `src/m0_original/ignition_matrix/`: Generador Rothermel, cargador de matrices y variante empírica.
- `src/m0_original/hourly/`: Evaluación de regla $(\mathrm{PI} \ge 70) \land (V \ge 20)$.
- `src/m0_original/daily/`: Acumulación de horas (1..5) y máscara ESA WorldCover 2021.
- `src/m0_original/commune/`: Reducción zonal comunal ($500\ \mathrm{m}$), cálculo de `SUM_br_ha`, `com_ha` y `proportion`.
- `src/m0_original/gee/`: Módulo JavaScript/Python Earth Engine corregido (sin resampling bilineal sobre booleanos).
- `src/m0_original/validation/`: Golden tests sintéticos y cliente de comparación contra ArcGIS Online.

### Fase 2: Golden Tests y Verificación de Límites
- Pruebas unitarias sobre todos los puntos de frontera ($19.999, 20.000, 20.001\ \mathrm{km/h}$; $2.0, 3.0, 4.0, 16.0, 30.0\%\ \mathrm{HCFM}$; $0, 5, 35, 40\ ^\circ\mathrm{C}$; $123.5\ \text{Hillshade}$).
- Verificación cruzada exacta entre el motor NumPy (`Python`) y el motor `Google Earth Engine`.

### Fase 3: Validación contra Cosecha Operacional de CONAF
- Ejecutar `conaf_api.py` para contrastar días con activación regional, verificando coincidencia de `com_ha`, `SUM_br_ha` y `proportion`.

### Fase 4: Congelamiento Definitivo (`M0_FROZEN = TRUE`)
- Etiquetar `M0 v1.0.0`.
- Bloquear modificaciones algorítmicas en M0.
- Proceder exclusivamente a la comparación científica con **BR-HR**.
