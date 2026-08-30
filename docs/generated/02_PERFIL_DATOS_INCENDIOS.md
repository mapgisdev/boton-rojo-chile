# 02 — Perfil Estructural y QA/QC del Consolidado de Incendios 2014–2024

Fecha de generación: 29 de agosto de 2026  
Fuente primaria: `insumos/Consolidado_incendios_2014_2024_temporada.csv`  
Responsables conceptuales: Data Scientist, Data Engineer, QA Engineer

---

## 1. Resumen Estructural del Dataset

El dataset histórico contiene el registro consolidado de ocurrencia y combate de incendios forestales de CONAF para 10 temporadas consecutivas (2014–2015 a 2023–2024).

| Métrica | Valor recalculado |
|---|---|
| **Total de filas (eventos)** | **68.546** |
| **Total de columnas** | **79** |
| **Formato y encoding** | CSV delimitado por `;`, codificación `UTF-8` sin BOM |
| **Tamaño en disco** | 49.872.706 bytes (~47,56 MB) |
| **Duplicados exactos de fila** | **0** |
| **Duplicados de identificador `index`** | **0** |
| **Rango temporal de inicio** | **2014-07-14 13:15:00** hasta **2024-06-28 16:10:00** |
| **Superficie total acumulada quemada** | **1.626.893,93 ha** |

---

## 2. Partición Temporal Obligatoria (Splits de Modelado)

Para evitar data leakage y asegurar una evaluación rigurosa fuera de muestra, el dataset se divide estrictamente por temporadas:

| Partición | Temporadas | N° Incendios | % del Total | Uso metodológico |
|---|---|---|---|---|
| **TRAIN** | 2014–2015 a 2020–2021 (7 temporadas) | **48.659** | 70,99 % | Entrenamiento de modelos, feature engineering y calibración |
| **VALIDATION** | 2021–2022 (1 temporada) | **6.947** | 10,13 % | Ajuste de hiperparámetros, selección de umbrales y champion/challenger |
| **TEST CIEGO** | 2022–2023 y 2023–2024 (2 temporadas) | **12.940** | 18,88 % | **Evaluación final cerrada** (sin tuning ni selección de variables) |
| **TOTAL** | **2014–2015 a 2023–2024** | **68.546** | **100,00 %** | — |

### Detalle por temporada anual:
- `2014 al 2015`: 8.073
- `2015 al 2016`: 6.784
- `2016 al 2017`: 5.274 (incluye mega-incendios de enero-febrero 2017)
- `2017 al 2018`: 6.081
- `2018 al 2019`: 7.219
- `2019 al 2020`: 8.127
- `2020 al 2021`: 7.101
- `2021 al 2022`: 6.947
- `2022 al 2023`: 6.982 (incluye incendios del centro-sur de febrero 2023)
- `2023 al 2024`: 5.958 (incluye incendios de Valparaíso de febrero 2024)

---

## 3. Distribución Horaria y Validación de Universos Temporales

Se evaluó la hora de `Inicio` para cada uno de los 68.546 incendios:

- **Incendios dentro de la ventana Botón Rojo (14:00–18:59):** **35.948 eventos (52,44 %)**
- **Incendios fuera de la ventana Botón Rojo (00:00–13:59 y 19:00–23:59):** **32.598 eventos (47,56 %)**

```text
Distribución horaria de inicio:
00:00:  1.110 ( 1,62 %)
01:00:    683 ( 1,00 %)
02:00:    475 ( 0,69 %)
03:00:    335 ( 0,49 %)
04:00:    260 ( 0,38 %)
05:00:    281 ( 0,41 %)
06:00:    463 ( 0,68 %)
07:00:    770 ( 1,12 %)
08:00:  1.030 ( 1,50 %)
09:00:  1.276 ( 1,86 %)
10:00:  1.907 ( 2,78 %)
11:00:  2.824 ( 4,12 %)
12:00:  4.070 ( 5,94 %)
13:00:  5.495 ( 8,02 %)
14:00:  7.141 (10,42 %) ──┐
15:00:  8.318 (12,13 %)   │
16:00:  8.038 (11,73 %)   ├─► BR-Window: 35.948 eventos (52,44 %)
17:00:  7.048 (10,28 %)   │
18:00:  5.403 ( 7,88 %) ──┘
19:00:  3.678 ( 5,37 %)
20:00:  2.520 ( 3,68 %)
21:00:  2.136 ( 3,12 %)
22:00:  1.842 ( 2,69 %)
23:00:  1.443 ( 2,11 %)
```

### Implicancia metodológica:
El 47,56 % de las igniciones ocurre fuera de la ventana 14–18 h. Por ende:
1. **Universo `BR-Window` (14:00–18:59):** Utilizado para auditar y validar directamente la regla Botón Rojo.
2. **Universo `Ignition-24h` (00:00–23:59):** Utilizado para el modelo probabilístico continuo $P(\mathrm{ignici\acute{o}n}_{h,t})$.

---

## 4. QA/QC Geográfico y Coordenadas

Se evaluaron los campos `Lat Calculada` y `Lon Calculada`:

| Condición | Registros | % | Acción en QA |
|---|---|---|---|
| **Coordenadas válidas dentro de Chile** | **68.536** | **99,99 %** | Aprobadas para mapeo a hexágonos H3 |
| **Coordenadas nulas (`NaN`)** | **8** | **0,01 %** | Se asignan por centroide comunal o se excluyen con flag `QA_NO_COORD` |
| **Outliers por error de tipeo** | **2** | **<0,01 %** | Se corrigen en capa derivada con flag de trazabilidad |

### Detalle de los 10 registros con anomalías geográficas:
1. `index=1522` (Maule, Empedrado): Coordenadas nulas.
2. `index=9386` (Maule, Parral): `Lat Calculada = -336.25` (tipeo en origen de `336°15'00" S`, latitud corregible a `-36.2500`).
3. `index=17857` (Biobío, Curanilahue): Coordenadas nulas.
4. `index=17893` (Biobío, Arauco): Coordenadas nulas.
5. `index=17894` (Biobío, Los Álamos): Coordenadas nulas.
6. `index=17895` (Biobío, Los Álamos): Coordenadas nulas.
7. `index=19084` (Araucanía, Purén): Coordenadas nulas.
8. `index=19128` (Araucanía, Carahue): Coordenadas nulas.
9. `index=25241` (Araucanía, Ercilla): `Lat Calculada = -0.065556` (tipeo en origen de `0°03'56" S`, latitud en Ercilla debería rondar `~-38.0°`).
10. `index=64526` (Biobío, Lota): Coordenadas nulas.

---

## 5. Distribución Espacial y Administrativa

### Distribución por Regiones:
- **Biobío:** 23.668 (34,53 %)
- **Araucanía:** 13.658 (19,93 %)
- **Maule:** 8.325 (12,15 %)
- **Valparaíso:** 6.889 (10,05 %)
- **Metropolitana:** 4.153 (6,06 %)
- **Ñuble:** 3.477 (5,07 %)
- **O'Higgins:** 3.020 (4,41 %)
- **Los Lagos:** 2.545 (3,71 %)
- **Los Ríos:** 1.225 (1,79 %)
- **Coquimbo:** 782 (1,14 %)
- **Aysén:** 310 (0,45 %)
- **Atacama:** 192 (0,28 %)
- **Magallanes:** 181 (0,26 %)
- **Arica y Parinacota:** 58 (0,08 %)
- **Tarapacá:** 32 (0,05 %)
- **Antofagasta:** 31 (0,05 %)

### Cobertura Comunal:
- **Comunas únicas (`Codcom`):** 319 comunas con ocurrencia registrada.
- **Nulos en `Codcom`:** 0.

---

## 6. Distribución de Superficie Afectada y Targets de Grandes Incendios

La distribución de tamaño de incendios presenta una asimetría extrema (distribución de colas pesadas tipo Pareto/Power Law):

- **Mínimo:** 0,00 ha (17 eventos con 0 ha registradas)
- **Mediana:** **0,39 ha**
- **Media:** **23,73 ha**
- **Percentil 90:** 7,75 ha
- **Percentil 95:** 23,00 ha
- **Percentil 99:** 244,63 ha
- **Máximo:** 159.812,58 ha (mega-incendio Las Máquinas, 2017)

### Conteo de Eventos por Umbral de Tamaño (Targets M3):
| Umbral | N° Eventos | % sobre Igniciones | Target Modelado |
|---|---|---|---|
| **$A > 0\ \mathrm{ha}$** | 68.528 | 99,97 % | Target $P(\mathrm{ignici\acute{o}n})$ |
| **$A > 10\ \mathrm{ha}$** | **5.681** | **8,29 %** | **Target $P(A > 10\ \mathrm{ha} \mid \mathrm{ignici\acute{o}n})$** |
| **$A > 50\ \mathrm{ha}$** | **2.045** | **2,98 %** | Target intermedio de severidad |
| **$A > 100\ \mathrm{ha}$** | **1.290** | **1,88 %** | **Target $P(A > 100\ \mathrm{ha} \mid \mathrm{ignici\acute{o}n})$** |
| **$A > 1.000\ \mathrm{ha}$** | **228** | **0,33 %** | Grandes incendios catastróficos |

---

## 7. Combustible Inicial y Causas

### Combustible Inicial Reportado:
- **Pastizal:** 27.052 (39,47 %)
- **Sin dato (`NaN`):** 17.693 (25,81 %)
- **Matorral:** 12.299 (17,94 %)
- **Desechos:** 4.223 (6,16 %)
- **Plantación eucalipto:** 2.403 (3,51 %)
- **Plantación pino:** 1.985 (2,90 %)
- **Arbolado natural:** 1.221 (1,78 %)
- **Cultivo agrícola:** 595 (0,87 %)
- **Otros / Basural:** 1.075 (1,57 %)

### Causas Principales:
- **Intencionales (2.1):** 26.200 (38,22 %)
- **Tránsito de personas / vehículos (1.7):** 16.716 (24,39 %)
- **Desconocida / En investigación (4.1):** 4.811 (7,02 %)
- **Faenas agrícolas / pecuarias (1.2):** 3.352 (4,89 %)
- **Faenas forestales (1.1):** 3.282 (4,79 %)
- **Quema de desechos (1.8):** 3.220 (4,70 %)
- **Accidentes eléctricos (1.9):** 2.070 (3,02 %)
- **Actividades recreativas (1.4):** 1.916 (2,79 %)
- **Otras / Combate / Estructurales:** 6.979 (10,18 %)
- **Naturales (Rayos):** < 0,5 %

> **Conclusión:** Más del 95 % de las causas conocidas son de origen antrópico (negligencia o intencionalidad). Esto respalda la necesidad científica de incorporar covariables de accesibilidad humana (distancia a caminos, interfaz urbano-rural y asentamientos) en los modelos probabilísticos de ignición.

---

## 8. Análisis de Calidad Cronológica e Inconsistencias Temporales

Se verificó el orden lógico de los hitos operacionales: $\text{Inicio} \le \text{Detección} \le \text{Aviso} \le \text{Despacho} \le \text{Arribo} \le \text{Primer Ataque} \le \text{Control} \le \text{Extinción}$:

- **Detección antes de Inicio:** 59 registros con timestamps invertidos.
- **Aviso antes de Detección:** 103 registros con timestamps invertidos.
- **Control antes de Inicio:** 79 registros con inconsistencia severa.
- **Extinción antes de Control:** 57 registros con inconsistencia severa.

Estas anomalías se documentarán y filtrarán con banderas QA específicas en la construcción del dataset derivado, sin alterar los datos fuente en `insumos/`.

---

## 9. Matriz de Riesgo de Data Leakage en los Campos del CSV

| Columna | Tipo / Momento de Disponibilidad | ¿Permitido como feature en $P(\mathrm{ignici\acute{o}n})$? | Justificación |
|---|---|---|---|
| `index`, `Región`, `Provincia`, `Comuna`, `Codcom` | Metadatos espaciales estáticos | **SÍ** | Información contextual previa |
| `Lat Calculada`, `Lon Calculada` | Coordenadas de inicio | **SÍ** (para mapeo H3) | Define la celda $h$ |
| `Inicio`, `temporada` | Timestamp de ocurrencia | **SÍ** (para tiempo $t$) | Define el instante temporal |
| `Temperatura`, `Humedad`, `Velocidad viento` (CSV) | Mediciones locales in situ / kestrel | **NO** en inferencia operacional | Solo como benchmark / QA retrospectivo |
| `Detección`, `Aviso`, `Despacho`, `Salida`, `Arribo`, `Primer ataque`, `Control`, `Extinción`, `Duración` | Tiempos de combate operacional | **PROHIBIDO** | **Data leakage temporal severo** (se conocen post-evento) |
| `Arribo Superficie`, `Primer ataque Superficie`, `Control Superficie`, `Superficie total`, `Subtotales` | Superficies observadas durante/post combate | **PROHIBIDO** en $P(\mathrm{IGN})$ | **Data leakage** (solo utilizable como target en M3) |
| `Causa General`, `Causa Específica`, `Predio`, `Propietario` | Determinación pericial posterior | **PROHIBIDO** | **Data leakage** (investigado días/meses después) |
