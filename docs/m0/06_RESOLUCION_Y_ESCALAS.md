# 06 — Resolución Espacial, Escalas y Remuestreo en el Modelo M0

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Componente:** Auditoría de Escalas Espaciales y Operaciones de Remuestreo M0  
**Fecha:** 30 de agosto de 2026  
**Responsables:** Senior Geospatial Architect, Scientific Reproducibility Auditor, GEE Specialist  

---

## 1. Identificación y Evidencia de las Dos Escalas Operacionales

El análisis forense de los servicios publicados por CONAF en ArcGIS Online revela la coexistencia de **dos escalas espaciales diferenciadas** dentro de la arquitectura del Botón Rojo oficial:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ 1. ESCALA_INDICE ≈ 2.000 m (Malla de Cálculo del Índice)                    │
│    - Tamaño de celda: 2.000 m x 2.000 m                                     │
│    - Área por polígono: 4.000.000 m² (EPSG:3857)                            │
│    - Evidencia empírica: Verificado en 100 % de los polígonos rasterizados   │
│      de las capas FeatureServer de TP, HC y PI de CONAF.                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ 2. ESCALA_ZONAL ≈ 500 m (Contabilidad de Superficie y Máscara Combustible)  │
│    - Tamaño de celda: 500 m x 500 m                                         │
│    - Área unitaria de cuantización: 25 ha (0.25 km²)                        │
│    - Evidencia empírica: Todos los valores del campo com_ha reportados en el │
│      servicio oficial Boton_Rojo son múltiplos exactos de 25 ha:             │
│      Colchane: 177.125 ha (7.085 celdas de 25 ha)                           │
│      Diego de Almagro: 21.550 ha (862 celdas de 25 ha)                      │
│      Camiña: 131.925 ha (5.277 celdas de 25 ha)                             │
│      Huara: 92.625 ha (3.705 celdas de 25 ha)                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Resolución Efectiva vs. Resolución Geométrica

Uno de los principales equívocos en la comunicación del Botón Rojo original es asumir que la grilla de $2\ \mathrm{km}$ representa una resolución física real:

| Insumo | Resolución Nativa | Resolución en M0 | Naturaleza del Remuestreo |
|---|---|---|---|
| **NOAA GFS** | $0.25^\circ \approx 25\text{ km}$ ($22\text{--}25\text{ km}$ en Chile) | $2.000\text{ m}$ | **Interpolación bilineal puramente geométrica**. No añade física de microescala, no resuelve brisas costeras ni vientos locales de quebrada (Puelche, Raco, Terral). |
| **SRTM DEM** | $90\text{ m}$ | $2.000\text{ m}$ | Reducción / muestreo a la grilla de cálculo del índice. |
| **ESA WorldCover** | $10\text{ m}$ | $500\text{ m}$ / $2.000\text{ m}$ | Remuestreo categórico (moda/cobertura mayoritaria) o reducción a máscara zonal de 500 m ($25\text{ ha}$). |
| **Límites DPA** | $1:50.000$ vectorial | Vectorial continuo | Intersección zonal mediante `reduceRegions` a escala 500 m. |

> **Conclusión de Teledetección:**  
> La resolución analítica real de la meteorología en M0 es de **25 km**, suavizada visualmente a **2 km**. Cualquier intento de atribuirle capacidad de micro-zonificación a M0 es físicamente insostenible.

---

## 3. Auditoría del Defecto de Interpolación Categórica en GEE

En el script heredado `work/m0_original/Boton_Rojo/codigo/boton_rojo_gee.js`, se detectó el siguiente patrón en la línea 192:

```javascript
return ee.Image.cat([t.rename('TP'), hr.rename('HR'), hcfm, viento, pi,
                     rfw.eq(2).rename('BR')])
         .resample('bilinear')
```

### Diagnóstico Forense
- Aplicar `.resample('bilinear')` a un conjunto de bandas apiladas que contiene capas categóricas y booleanas discretas (`BR`, `RFW`, `PI`) produce **valores decimales continuos espurios** en las zonas de transición (p. ej. valores intermedios de $0.34$, $0.72$ en lugar del binario $0$ o $1$ de activación).
- **Corrección requerida en el Baseline M0:**
  El remuestreo bilineal debe aplicarse **únicamente a las bandas meteorológicas continuas de entrada** ($T, \mathrm{HR}, u_{10}, v_{10}$) a escala de $2.000\text{ m}$. Todas las reclasificaciones (A a G), la consulta de matriz PI, la condición booleana $\mathrm{BR}_t$ y el conteo de horas deben ejecutarse de forma estrictamente discreta sobre la grilla ya remuestreada.

---

## 4. Tratamiento de Celdas de Borde y Proyecciones

1. **Cálculo de Área en GEE:**  
   - En GEE se utiliza `ee.Image.pixelArea()`, que calcula geodésicamente el área real en $\mathrm{m}^2$ en el elipsoide WGS84, dividiéndola por $10.000$ para obtener hectáreas exactas ajustadas por latitud.
2. **Cálculo de Área en Python (`pipeline.py`):**  
   - Se realiza sobre grilla en EPSG:4326, aplicando la corrección meridiana y paralela:
     $$\Delta y = \Delta \mathrm{lat} \times 111.320\text{ m}$$
     $$\Delta x = \Delta \mathrm{lon} \times 111.320\text{ m} \times \cos(\mathrm{lat})$$
     $$\mathrm{Area}_{\mathrm{ha}} = \frac{\Delta x \cdot \Delta y}{10.000}$$
3. **Células Parcialmente Incluidas en Comunas:**  
   - La reducción zonal con `ee.Reducer.sum()` sobre polígonos comunales a escala de 500 m asigna el peso del píxel según su centroide o intersección fraccional ponderada por la máscara de combustible.
