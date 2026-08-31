# 01 — Metodología Original Reconstruida del Botón Rojo CONAF (Línea Base M0)

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Componente:** Especificación Teórica y Matemática de M0  
**Fecha:** 30 de agosto de 2026  
**Responsables:** Fire Science Reviewer, Senior Geospatial Architect, Scientific Reproducibility Auditor  

---

## 1. Definición Institucional y Propósito Operativo

El **Botón Rojo** es una herramienta de pronóstico preventivo a escala regional y comunal creada en 2018 por el Departamento de Desarrollo e Investigación (DEI) de la Gerencia de Protección contra Incendios Forestales (GEPRIF) de la Corporación Nacional Forestal (CONAF). En 2023 se migró a Google Earth Engine y ArcGIS Online.

### Propósito
Identificar celdas territoriales y comunas donde confluyen condiciones meteorológicas, topográficas y de humedad del combustible que generan una probabilidad crítica de ignición y propagación rápida, configurando escenarios de alta dificultad para el combate y control de incendios.

### Naturaleza Jurídica
El Botón Rojo **no constituye una alerta civil en sí mismo**, sino un insumo técnico de pronóstico que CONAF transfiere al Servicio Nacional de Prevención y Respuesta ante Desastres (SENAPRED), sobre el cual este organismo decreta Alertas Tempranas Preventivas (ATP) de conformidad con la Ley N° 21.364.

---

## 2. Insumos Primarios del Sistema Original

El sistema oficial se fundamenta en cuatro conjuntos de datos abiertos:

1. **Pronóstico Meteorológico Numérico:**  
   - Modelo: NOAA GFS (Global Forecast System) a $0.25^\circ$ ($\approx 25\text{ km}$ en latitud de Chile).  
   - Colección Earth Engine: `NOAA/GFS0P25`.  
   - Variables requeridas a 2 m y 10 m sobre el terreno:
     - `temperature_2m_above_ground` ($T$, en $^\circ\text{C}$ o $\text{K}$).
     - `relative_humidity_2m_above_ground` ($HR$, en $\%$).
     - `u_component_of_wind_10m_above_ground` ($u_{10}$, en $\text{m/s}$).
     - `v_component_of_wind_10m_above_ground` ($v_{10}$, en $\text{m/s}$).

2. **Modelo Digital de Elevación (DEM):**  
   - Sensor: Shuttle Radar Topography Mission (SRTM 90 m v4 / CGIAR).  
   - Colección Earth Engine: `CGIAR/SRTM90_V4`.  
   - Uso: Cálculo de sombreado topográfico (*hillshade*) con azimut $313^\circ$ y elevación solar $60^\circ$.

3. **Cobertura de Suelo (Máscara de Combustible):**  
   - Cartografía: ESA WorldCover v200 (año 2021) a 10 m de resolución espacial.  
   - Colección Earth Engine: `ESA/WorldCover/v200`.  
   - Clases seleccionadas como combustible activo:
     - Clase 10: Árboles / Bosques (*Trees*)
     - Clase 20: Matorrales (*Shrubland*)
     - Clase 30: Pastizales (*Grassland*)
     - Clase 40: Cultivos agrícolas (*Cropland*)
     - Clase 90: Humedales herbáceos (*Herbaceous wetland*)

4. **Límites Político-Administrativos:**  
   - División Político-Administrativa de Chile (SUBDERE, IGM, INE, versión 2023).  
   - Atributos clave: `COMUNA` (código único territorial CUT) y `NOM_COMUNA`.

---

## 3. Cadena de Transformación Matemática y Espacial

La secuencia original se estructura en 7 pasos algorítmicos secuenciales:

```text
 NOAA GFS 0.25° (Última corrida disponible)
     │
     ├── Extracción ventana 14:00–18:59 local (5 pasos horarios: 14, 15, 16, 17, 18 h)
     │
     ├── T2m (°C), HR2m (%), u10 (m/s), v10 (m/s)
     │
     ├─► 1. HCFM = 0.297374 + 0.262·HR − 0.00982·T   (Regresión U. de Chile)
     ├─► 2. Viento = √(u10² + v10²) · 3.6            (km/h a 10 m)
     ├─► 3. Hillshade(SRTM 90m, az=313°, alt=60°)
     │        └─► Reclass G: Hillshade ≤ 123.5 -> 200 (Sombra), > 123.5 -> 100 (Expuesto)
     │
     ├─► 4. Construcción de Clave Compuesta:
     │        Clave = ReclassC(HCFM) [2000..17000]
     │              + ReclassG(Hillshade) [100 | 200]
     │              + ReclassA(T) [1..9]
     │
     ├─► 5. Probabilidad de Ignición (PI):
     │        PI = MATRIZ_PI[Clave]                  (Tabla de 288 celdas, rango 0..100 %)
     │
     ├─► 6. Regla de Activación Horaria por Píxel:
     │        BR_t = (PI_t ≥ 70 %) ∧ (Viento_t ≥ 20 km/h)   (Condición binaria)
     │
     ├─► 7. Agregación Diaria y Filtrado de Combustible:
     │        Horas_BR = ∑ (BR_t para t = 14..18)           (Valores enteros 0, 1, 2, 3, 4, 5)
     │        Horas_BR_Filtrado = Horas_BR · Máscara_Combustible  (Clases 10, 20, 30, 40, 90)
     │
     └─► 8. Reducción Zonal Comunal (por cada día d0..d4 y por cada clase de horas 1..5):
              - SUM_br_ha: Área (ha) de la comuna que cumple exactamente H horas de BR
              - com_ha: Superficie combustible total de la comuna (ha)
              - proportion = SUM_br_ha / com_ha
```

---

## 4. Ecuaciones Físicas de la Metodología

### 4.1. Humedad del Combustible Fino Muerto (HCFM)
Derivada por la Facultad de Ciencias Forestales de la Universidad de Chile (adoptada por CONAF y documentada en NASA DEVELOP 2022):

$$\mathrm{HCFM} = 0.297374 + 0.262 \cdot \mathrm{HR} - 0.00982 \cdot T$$

- $\mathrm{HR} \in [1, 100]\%$ (Humedad relativa a 2 m).
- $T \in [^\circ\mathrm{C}]$ (Temperatura del aire a 2 m).
- Salida en $\%$ base peso seco.

### 4.2. Velocidad Escalar del Viento a 10 m
Módulo euclidiano de las componentes horizontal y vertical provistas por GFS en $\text{m/s}$, escaladas a $\text{km/h}$:

$$V_{10} = \sqrt{u_{10}^2 + v_{10}^2} \times 3.6$$

### 4.3. Sombreado Topográfico (*Hillshade*)
Calculado sobre el elipsoide WGS84 utilizando pendientes y orientaciones locales derivadas de SRTM:

$$\mathrm{Hillshade} = 255 \cdot \Big( \cos(\theta_z) \cos(\mathcal{S}) + \sin(\theta_z) \sin(\mathcal{S}) \cos(\alpha_s - \mathcal{A}) \Big)$$

donde:
- $\theta_z = 90^\circ - 60^\circ = 30^\circ$ (Ángulo cenital solar).
- $\alpha_s = 360^\circ - 313^\circ + 90^\circ = 137^\circ$ (Azimut astronómico transformado a convención matemática).
- $\mathcal{S}$: Pendiente del terreno (*slope*, en radianes).
- $\mathcal{A}$: Orientación de la ladera (*aspect*, en radianes).

---

## 5. La Regla de Activación y Agregación Espacio-Temporal

### Condición Horaria Binaria
En cada paso horario $t \in \{14, 15, 16, 17, 18\}$, una celda se activa si y solo si:

$$\mathrm{BR}(x, y, t) = \begin{cases} 1 & \text{si } \mathrm{PI}(x, y, t) \ge 70\% \ \land \ V_{10}(x, y, t) \ge 20\text{ km/h} \\ 0 & \text{en caso contrario} \end{cases}$$

### Sumatoria Diaria de Horas Críticas
Para cada celda espacial $(x, y)$ y día de pronóstico $d \in \{d_0, d_1, d_2, d_3, d_4\}$:

$$\mathrm{HorasBR}(x, y, d) = \sum_{t=14}^{18} \mathrm{BR}(x, y, d, t) \quad \in \{0, 1, 2, 3, 4, 5\}$$

### Enmascaramiento de Cobertura
Las celdas con $\mathrm{HorasBR} > 0$ se intersectan con la máscara booleana de combustible:

$$\mathrm{Activo}(x, y, d) = \mathrm{HorasBR}(x, y, d) \cdot \mathbf{1}_{\mathrm{Combustible}}(x, y)$$

---

## 6. Salida Oficial Comunal

Para cada comuna $c$, día $d$ y categoría de horas $h \in \{1, 2, 3, 4, 5\}$:

1. **`SUM_br_ha`**:
   $$\mathrm{SUM\_br\_ha}(c, d, h) = \iint_{(x,y) \in c} \mathbf{1}_{\{\mathrm{Activo}(x, y, d) = h\}} \, dA$$
2. **`com_ha`**:
   $$\mathrm{com\_ha}(c) = \iint_{(x,y) \in c} \mathbf{1}_{\mathrm{Combustible}}(x, y) \, dA$$
3. **`proportion`**:
   $$\mathrm{proportion}(c, d, h) = \frac{\mathrm{SUM\_br\_ha}(c, d, h)}{\mathrm{com\_ha}(c)}$$

El resultado se publica con 5 días de horizonte ($d_0, d_1, d_2, d_3, d_4$) en la tabla comunal del servicio oficial `Boton_Rojo`.
