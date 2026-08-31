# 03 — Cadena de Cálculo Detallada del Modelo M0

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Componente:** Flujo de Procesamiento y Algoritmo Paso a Paso de M0  
**Fecha:** 30 de agosto de 2026  
**Responsables:** Senior Geospatial Architect, Fire Science Reviewer, Backend Engineer  

---

## 1. Diagrama de la Cadena de Procesamiento Oficial

```text
               ┌──────────────────────────────────────────────┐
               │         NOAA GFS 0.25° (Última corrida)      │
               │  temperature_2m, relative_humidity_2m, u, v  │
               └──────────────────────┬───────────────────────┘
                                      │
                                      ▼
               ┌──────────────────────────────────────────────┐
               │    Ventana Crítica Vespertina (14:00–18:59)  │
               │   5 Pasos Horarios Locales: 14, 15, 16, 17, 18│
               └──────────────────────┬───────────────────────┘
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           │                          │                          │
           ▼                          ▼                          ▼
┌──────────────────────┐   ┌──────────────────────┐   ┌──────────────────────┐
│ Temperatura T2m (°C) │   │ Humedad Relativa (%) │   │  Viento (u10, v10)   │
└──────────┬───────────┘   └──────────┬───────────┘   └──────────┬───────────┘
           │                          │                          │
           │                          ▼                          ▼
           │               ┌──────────────────────┐   ┌──────────────────────┐
           │               │     Cálculo HCFM     │   │   Viento Escalar     │
           │               │ 0.297+0.262·HR-0.0098·T  │   │   √(u²+v²) · 3.6     │
           │               └──────────┬───────────┘   └──────────┬───────────┘
           │                          │                          │
           ▼                          ▼                          │
┌──────────────────────┐   ┌──────────────────────┐              │
│      Reclass A       │   │      Reclass C       │              │
│    Clases 1 a 9      │   │ Millares 2000..17000 │              │
└──────────┬───────────┘   └──────────┬───────────┘              │
           │                          │                          │
           │       ┌──────────────────┴───────────────────┐      │
           │       │   SRTM DEM 90m -> Hillshade(313°,60°)│      │
           │       │   Reclass G: ≤123.5->200, >123.5->100│      │
           │       └──────────────────┬───────────────────┘      │
           │                          │                          │
           └──────────────────────────┼──────────────────────────┘
                                      ▼
                      ┌────────────────────────────────┐
                      │    CLAVE COMPUESTA ÍNDICE      │
                      │  Clave = ReclassC + G + A      │
                      │    (288 Combinaciones)         │
                      └───────────────┬────────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │    MATRIZ PROBABILIDAD (PI)    │
                      │       PI = MATRIZ[Clave]       │
                      │        (Valores 0–100 %)       │
                      └───────────────┬────────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │   CONDICIÓN HORARIA BR (RFW=2) │
                      │  (PI ≥ 70 %) ∧ (Viento ≥ 20)   │
                      └───────────────┬────────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │       ACUMULACIÓN DIARIA       │
                      │   HorasBR = ∑ BR_t  (1..5)     │
                      └───────────────┬────────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │     MÁSCARA DE COMBUSTIBLE     │
                      │ ESA WorldCover (10,20,30,40,90)│
                      └───────────────┬────────────────┘
                                      │
                                      ▼
                      ┌────────────────────────────────┐
                      │   ESTADÍSTICA ZONAL COMUNAL    │
                      │ Por cada Comuna, Día y Hora:   │
                      │  - SUM_br_ha                   │
                      │  - com_ha (Combustible)        │
                      │  - proportion                  │
                      └────────────────────────────────┘
```

---

## 2. Descripción Paso a Paso del Flujo de Ejecución

### Paso 1: Ingesta y Filtrado Temporal del Pronóstico GFS
- Se descarga o consulta en GEE la colección `NOAA/GFS0P25` filtrada por la corrida más reciente (`creation_time`).
- Se seleccionan las horas de pronóstico (`forecast_hours`) comprendidas entre 1 y 120 h (hasta 5 días: $d_0, d_1, d_2, d_3, d_4$).
- Se convierten las marcas de tiempo UTC a hora local de Chile (`America/Santiago`), considerando el desfase estacional (UTC-3 en verano austral, UTC-4 en invierno).
- Se seleccionan exactamente los 5 pasos horarios vespertinos: $t \in \{14:00, 15:00, 16:00, 17:00, 18:00\}$.

### Paso 2: Cálculo de Variables Físicas Derivadas
Para cada paso horario $t$:
1. **Temperatura ($T$):** Se extrae en grados Celsius ($T = T_{\mathrm{kelvin}} - 273.15$ si viene en Kelvin).
2. **Humedad Relativa ($\mathrm{HR}$):** Se satura en el rango $[1, 100]\%$.
3. **Velocidad del Viento ($V$):** Se calcula a partir de las componentes $u_{10}$ y $v_{10}$:
   $$V = \sqrt{u_{10}^2 + v_{10}^2} \times 3.6 \quad [\mathrm{km/h}]$$
4. **Humedad del Combustible Fino Muerto ($\mathrm{HCFM}$):** Se aplica la fórmula empírica de equilibrio de la U. de Chile:
   $$\mathrm{HCFM} = 0.297374 + 0.262 \cdot \mathrm{HR} - 0.00982 \cdot T \quad [\%]$$

### Paso 3: Sombreado Topográfico y Reclasificación G
- Se calcula el sombreado sobre el DEM SRTM de 90 m con azimut solar de $313^\circ$ (noroeste) y ángulo de elevación solar de $60^\circ$.
- Se reclasifica en dos estados de exposición solar mediante la regla:
  $$\mathrm{ReclassG}(\mathrm{Hillshade}) = \begin{cases} 200 & \text{si } \mathrm{Hillshade} \le 123.5 \text{ (Sombreado)} \\ 100 & \text{si } \mathrm{Hillshade} > 123.5 \text{ (Expuesto)} \end{cases}$$

### Paso 4: Construcción de la Clave Compuesta de Indexación
Se combinan las tres clasificaciones espaciales en un único identificador entero:
$$\mathrm{Clave} = \mathrm{ReclassC}(\mathrm{HCFM}) + \mathrm{ReclassG}(\mathrm{Hillshade}) + \mathrm{ReclassA}(T)$$
- $\mathrm{ReclassC}(\mathrm{HCFM}) \in \{2000, 3000, \dots, 17000\}$ (16 niveles de humedad).
- $\mathrm{ReclassG}(\mathrm{Hillshade}) \in \{100, 200\}$ (2 estados solares).
- $\mathrm{ReclassA}(T) \in \{1, 2, \dots, 9\}$ (9 clases de temperatura).
- Rango total de claves posibles: 288 valores enteros discretos (desde 2101 hasta 17209). Si los valores caen fuera de dominio ($T > 40\ ^\circ\mathrm{C}$ o $\mathrm{HCFM} > 30\%$), la clave resulta en 0 / NoData.

### Paso 5: Asignación de Probabilidad de Ignición (PI)
A cada celda con clave válida se le asigna el valor de probabilidad correspondiente de la matriz:
$$\mathrm{PI} = \mathrm{MATRIZ\_PI}[\mathrm{Clave}] \quad \in [0.0, 100.0]\%$$

### Paso 6: Evaluación de la Condición Horaria de Botón Rojo
En cada hora $t$, se evalúa la condición de activación simultánea:
$$\mathrm{BR}_t = (\mathrm{PI}_t \ge 70.0) \land (V_t \ge 20.0)$$

### Paso 7: Acumulación Temporal Diaria y Máscara de Combustible
- Para cada día de pronóstico ($d_0 \dots d_4$), se suma el número de horas en que se cumplió la condición:
  $$\mathrm{HorasBR} = \sum_{t=14}^{18} \mathrm{BR}_t \quad \in \{0, 1, 2, 3, 4, 5\}$$
- Se aplica la máscara binaria de cobertura ESA WorldCover v200 (clases 10, 20, 30, 40, 90). Las celdas sin combustible o con $\mathrm{HorasBR} = 0$ quedan enmascaradas.

### Paso 8: Estadística Zonal Comunal Oficial
Para cada comuna $c$, día $d$ y valor de horas $h \in \{1, 2, 3, 4, 5\}$:
- $\mathrm{SUM\_br\_ha}$: Suma del área en hectáreas de los píxeles dentro de la comuna que presentan exactamente $h$ horas de Botón Rojo.
- $\mathrm{com\_ha}$: Superficie combustible total de la comuna (constante para cada comuna).
- $\mathrm{proportion}$: Cociente $\frac{\mathrm{SUM\_br\_ha}}{\mathrm{com\_ha}}$.
