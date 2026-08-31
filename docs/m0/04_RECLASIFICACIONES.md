# 04 — Tablas de Reclasificación del Modelo Legado M0 (Reclass A a G)

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Componente:** Especificación Numérica de Reclasificaciones M0  
**Fecha:** 30 de agosto de 2026  
**Responsables:** Fire Science Reviewer, QA Engineer, Senior Geospatial Architect  

---

## 1. Fundamento de las Reclasificaciones

El modelo original de CONAF utiliza siete tablas de reclasificación discretas para traducir variables continuas en clases simbólicas y claves de indexación. Estas tablas provienen del apéndice técnico de NASA DEVELOP (2022) y fueron verificadas contra las leyendas y metadatos de los Feature Services públicos de CONAF (`TP`, `HC`, `PI`, `VV`, `Boton_Rojo`).

---

## 2. Detalle Exhaustivo de las Siete Tablas

### 2.1. Reclass A — Temperatura del Aire ($T$ en $^\circ\mathrm{C}$)
- **Propósito:** Codificar la temperatura para las unidades ($1 \dots 9$) de la clave compuesta de la matriz PI.
- **Capa pública asociada:** `TP` (Temperatura).
- **Convención de límites:** Intervalos semiabiertos por la izquierda $(L_{inf}, L_{sup}]$, salvo la clase 1 que incluye todos los valores $\le 0$.

| Clase | Rango ($^\circ\mathrm{C}$) | Límite Matemático | Representante ($^\circ\mathrm{C}$) | Etiqueta Pública |
|:---:|:---:|:---:|:---:|:---:|
| **1** | Menor a 0 | $T \le 0.0$ | -2.5 | Menor a 0 |
| **2** | 0 a 5 | $0.0 < T \le 5.0$ | 2.5 | 0 - 5 |
| **3** | 5 a 10 | $5.0 < T \le 10.0$ | 7.5 | 5 - 10 |
| **4** | 10 a 15 | $10.0 < T \le 15.0$ | 12.5 | 10 - 15 |
| **5** | 15 a 20 | $15.0 < T \le 20.0$ | 17.5 | 15 - 20 |
| **6** | 20 a 25 | $20.0 < T \le 25.0$ | 22.5 | 20 - 25 |
| **7** | 25 a 30 | $25.0 < T \le 30.0$ | 27.5 | 25 - 30 |
| **8** | 30 a 35 | $30.0 < T \le 35.0$ | 32.5 | 30 - 35 |
| **9** | 35 a 40 | $35.0 < T \le 40.0$ | 37.5 | Mayor a 35 |

> **Comportamiento de borde en $T > 40\ ^\circ\mathrm{C}$:**  
> En la herramienta `Reclassify` original de ArcGIS, los valores mayores a 40 °C no tenían clase asignada y pasaban a `NoData`. En la implementación M0 fiel se mantiene esta restricción, documentando que en olas de calor extremas el modelo original apagaba el píxel por defecto de diseño de la tabla.

---

### 2.2. Reclass B — Humedad del Combustible Fino Muerto ($\mathrm{HCFM}$ en $\%$) para Visualización
- **Propósito:** Generar la simbología de la capa temática institucional `HC`.
- **Capa pública asociada:** `HC` (Humedad del Combustible Fino Muerto).

| Clase | Rango ($\%$) | Límite Matemático | Etiqueta Oficial |
|:---:|:---:|:---:|:---:|
| **1** | 0 a 2 | $\mathrm{HCFM} \le 2.0$ | 0 - 2 |
| **2** | 2 a 4 | $2.0 < \mathrm{HCFM} \le 4.0$ | 2 - 4 |
| **3** | 4 a 6 | $4.0 < \mathrm{HCFM} \le 6.0$ | 4 - 6 |
| **4** | 6 a 8 | $6.0 < \mathrm{HCFM} \le 8.0$ | 6 - 8 |
| **5** | 8 a 10 | $8.0 < \mathrm{HCFM} \le 10.0$ | 8 - 10 |
| **6** | 10 a 12 | $10.0 < \mathrm{HCFM} \le 12.0$ | 10 - 12 |
| **7** | 12 a 15 | $12.0 < \mathrm{HCFM} \le 15.0$ | 12 - 15 |
| **8** | 15 a 20 | $15.0 < \mathrm{HCFM} \le 20.0$ | 15 - 20 |
| **9** | 20 a 25 | $20.0 < \mathrm{HCFM} \le 25.0$ | 20 - 25 |
| **10** | Mayor a 25 | $\mathrm{HCFM} > 25.0$ | Mayor a 25 |

---

### 2.3. Reclass C — $\mathrm{HCFM}$ ($\%$) para Clave de Indexación de Matriz PI
- **Propósito:** Codificar los millares ($2000 \dots 17000$) de la clave compuesta que indexa las 16 filas de humedad de la tabla NFDRS / Rothermel.
- **Fórmula matemática equivalente:** $1000 \cdot \lceil \mathrm{HCFM} \rceil$ acotado en $[2000, 17000]$.

| Clase de Millares | Intervalo de $\mathrm{HCFM}$ ($\%$) | Límite Matemático | Humedad Representativa |
|:---:|:---:|:---:|:---:|
| **2000** | $\le 2$ | $\mathrm{HCFM} \le 2.0$ | 2.0 % |
| **3000** | 2 a 3 | $2.0 < \mathrm{HCFM} \le 3.0$ | 3.0 % |
| **4000** | 3 a 4 | $3.0 < \mathrm{HCFM} \le 4.0$ | 4.0 % |
| **5000** | 4 a 5 | $4.0 < \mathrm{HCFM} \le 5.0$ | 5.0 % |
| **6000** | 5 a 6 | $5.0 < \mathrm{HCFM} \le 6.0$ | 6.0 % |
| **7000** | 6 a 7 | $6.0 < \mathrm{HCFM} \le 7.0$ | 7.0 % |
| **8000** | 7 a 8 | $7.0 < \mathrm{HCFM} \le 8.0$ | 8.0 % |
| **9000** | 8 a 9 | $8.0 < \mathrm{HCFM} \le 9.0$ | 9.0 % |
| **10000** | 9 a 10 | $9.0 < \mathrm{HCFM} \le 10.0$ | 10.0 % |
| **11000** | 10 a 11 | $10.0 < \mathrm{HCFM} \le 11.0$ | 11.0 % |
| **12000** | 11 a 12 | $11.0 < \mathrm{HCFM} \le 12.0$ | 12.0 % |
| **13000** | 12 a 13 | $12.0 < \mathrm{HCFM} \le 13.0$ | 13.0 % |
| **14000** | 13 a 14 | $13.0 < \mathrm{HCFM} \le 14.0$ | 14.0 % |
| **15000** | 14 a 15 | $14.0 < \mathrm{HCFM} \le 15.0$ | 15.0 % |
| **16000** | 15 a 16 | $15.0 < \mathrm{HCFM} \le 16.0$ | 16.0 % |
| **17000** | 16 a 30 | $16.0 < \mathrm{HCFM} \le 30.0$ | 17.0 % |

> **Borde de Dominio:** $\mathrm{HCFM} > 30.0\%$ produce clave 0 (`NoData`), dado que sobre $30\%$ de humedad el combustible fino no puede mantener ignición sostenida.

---

### 2.4. Reclass D — Probabilidad de Ignición ($\mathrm{PI}$ en $\%$) para Visualización
- **Propósito:** Reclasificar la probabilidad en deciles $1 \dots 10$ para la capa temática `PI`.
- **Capa pública asociada:** `PI` (Probabilidad de Ignición).

| Decil | Rango de PI ($\%$) | Límite Matemático | Etiqueta Oficial |
|:---:|:---:|:---:|:---:|
| **1** | 0 a 10 | $\mathrm{PI} \le 10.0$ | 10 |
| **2** | 10 a 20 | $10.0 < \mathrm{PI} \le 20.0$ | 20 |
| **3** | 20 a 30 | $20.0 < \mathrm{PI} \le 30.0$ | 30 |
| **4** | 30 a 40 | $30.0 < \mathrm{PI} \le 40.0$ | 40 |
| **5** | 40 a 50 | $40.0 < \mathrm{PI} \le 50.0$ | 50 |
| **6** | 50 a 60 | $50.0 < \mathrm{PI} \le 60.0$ | 60 |
| **7** | 60 a 70 | $60.0 < \mathrm{PI} \le 70.0$ | 70 |
| **8** | 70 a 80 | $70.0 < \mathrm{PI} \le 80.0$ | 80 |
| **9** | 80 a 90 | $80.0 < \mathrm{PI} \le 90.0$ | 90 |
| **10** | 90 a 100 | $90.0 < \mathrm{PI} \le 100.0$ | 100 |

---

### 2.5. Reclass E — Velocidad del Viento ($V$ en $\mathrm{km/h}$) para Visualización
- **Propósito:** Generar las 8 clases temáticas de la capa pública `VV`.
- **Capa pública asociada:** `VV` (Velocidad del Viento).

| Clase | Rango ($\mathrm{km/h}$) | Límite Matemático | Etiqueta Oficial |
|:---:|:---:|:---:|:---:|
| **1** | 0 a 3 | $V \le 3.0$ | Calmo |
| **2** | 3 a 5 | $3.0 < V \le 5.0$ | 3 - 5 |
| **3** | 5 a 10 | $5.0 < V \le 10.0$ | 5 - 10 |
| **4** | 10 a 15 | $10.0 < V \le 15.0$ | 10 - 15 |
| **5** | 15 a 20 | $15.0 < V \le 20.0$ | 15 - 20 |
| **6** | 20 a 25 | $20.0 < V \le 25.0$ | 20 - 25 |
| **7** | 25 a 30 | $25.0 < V \le 30.0$ | 25 - 30 |
| **8** | Mayor a 30 | $V > 30.0$ | Mayor a 30 |

---

### 2.6. Reclass F — Viento Binario para Regla de Botón Rojo
- **Propósito:** Aplicar el umbral crítico de velocidad del viento ($20\ \mathrm{km/h}$) en la lógica horaria.

| Valor Salida | Condición Matemática | Significado Operativo |
|:---:|:---:|:---:|
| **0** | $V < 20.0\ \mathrm{km/h}$ | Viento no crítico |
| **1** | $V \ge 20.0\ \mathrm{km/h}$ | Viento en condición de activación BR |

---

### 2.7. Reclass G — Sombreado Topográfico (*Hillshade*)
- **Propósito:** Codificar las centenas ($100$ o $200$) de la clave compuesta según la exposición solar del terreno.
- **Parámetros del Hillshade:** DEM SRTM 90 m, Azimut $313^\circ$, Altitud solar $60^\circ$. Rango de salida: $0 \dots 255$.

| Código Salida | Rango de Hillshade | Estado de Exposición |
|:---:|:---:|:---:|
| **200** | $\mathrm{Hillshade} \le 123.5$ | Sombreado (*Shaded*) |
| **100** | $\mathrm{Hillshade} > 123.5$ | Expuesto al sol (*Unshaded*) |

---

## 3. Vectores de Prueba en Puntos Críticos de Frontera

Para garantizar reproducibilidad determinista, la suite de pruebas unitarias debe verificar rigurosamente los siguientes valores en los bordes de decisión:

```text
Viento (km/h):
  19.999 -> ReclassE = 5, ReclassF = 0 (NO activa)
  20.000 -> ReclassE = 5, ReclassF = 1 (ACTIVA)
  20.001 -> ReclassE = 6, ReclassF = 1 (ACTIVA)

HCFM (%):
   2.000 -> ReclassC = 2000
   2.001 -> ReclassC = 3000
   4.000 -> ReclassC = 4000
   4.001 -> ReclassC = 5000
  16.000 -> ReclassC = 16000
  16.001 -> ReclassC = 17000
  30.000 -> ReclassC = 17000
  30.001 -> ReclassC = 0 (NoData / Fuera de Dominio)

Temperatura (°C):
   0.000 -> ReclassA = 1
   0.001 -> ReclassA = 2
  35.000 -> ReclassA = 8
  35.001 -> ReclassA = 9
  40.000 -> ReclassA = 9
  40.001 -> ReclassA = 0 (NoData / Fuera de Dominio)

Hillshade:
 123.500 -> ReclassG = 200 (Sombreado)
 123.501 -> ReclassG = 100 (Expuesto)
```
