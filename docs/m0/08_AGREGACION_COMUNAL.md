# 08 — Metodología de Agregación Zonal Comunal en M0

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Componente:** Reducción Zonal, Esquema de Datos y Métricas Comunales M0  
**Fecha:** 30 de agosto de 2026  
**Responsables:** Senior Geospatial Architect, Data Engineer, Fire Science Reviewer  

---

## 1. Distinción Crítica: Raster Previo vs. Clasificación Comunal

Un error conceptual frecuente en la literatura secundaria es modelar el Botón Rojo como un promedio comunal de variables continuas:

$$\textbf{INCORRECTO: } \quad \text{Raster } \mathrm{PI}(x,y) \longrightarrow \overline{\mathrm{PI}}_{\mathrm{comuna}} \longrightarrow \text{¿} \overline{\mathrm{PI}} \ge 70\% \text{?}$$

La arquitectura original confirmada y verificada en CONAF opera de forma completamente distinta:

$$\textbf{CORRECTO: } \quad \begin{array}{c} \text{Variables meteorológicas por celda} \\ \Downarrow \\ \mathrm{PI}(x,y,t) \text{ por celda} \\ \Downarrow \\ \mathrm{BR}_t(x,y) = (\mathrm{PI} \ge 70 \land V \ge 20) \text{ binario por celda y hora} \\ \Downarrow \\ \mathrm{HorasBR}(x,y) = \sum_{t=14}^{18} \mathrm{BR}_t(x,y) \in \{0,1,2,3,4,5\} \\ \Downarrow \\ \text{Filtrado por Máscara Combustible (ESA WorldCover)} \\ \Downarrow \\ \text{Reducción Zonal de Área por Categoría de Horas en cada Comuna} \end{array}$$

---

## 2. Esquema Oficial del Servicio Comunal `Boton_Rojo`

El Feature Service publicado por CONAF (`services5.arcgis.com/A1ELWse9bRAi2JiV/.../Boton_Rojo`) presenta exactamente las siguientes columnas:

| Campo | Tipo de Dato | Significado Metodológico Confirmado |
|---|---|---|
| `date` | `Date` (YYYY-MM-DD) | Fecha de validez del pronóstico para la ventana vespertina (14:00–18:59). |
| `horas` | `Integer` ($1 \dots 5$) | Número exacto de pasos horarios vespertinos en que las celdas cumplieron la condición BR. |
| `com_id` | `String` / `Integer` | Código Único Territorial (CUT) de la comuna según la DPA oficial de Chile. |
| `com` | `String` | Nombre oficial de la comuna. |
| `prov` | `String` | Nombre de la provincia a la que pertenece la comuna. |
| `reg` | `String` | Nombre de la región político-administrativa. |
| `nom_minrel` | `String` | Nombre normalizado para interoperabilidad ministerial. |
| `com_ha` | `Float` ($\text{ha}$) | **Superficie COMBUSTIBLE de la comuna**, calculada como la suma de píxeles clasificados como combustible (ESA WorldCover 10, 20, 30, 40, 90). **No es la superficie total administrativa**. |
| `SUM_br_ha` | `Float` ($\text{ha}$) | Superficie de la comuna (en hectáreas) que registra exactamente ese número de `horas` de Botón Rojo en el día `date`. |
| `proportion` | `Float` ($0.0 \dots 1.0$) | Razón matemática exacta: $\mathrm{proportion} = \frac{\mathrm{SUM\_br\_ha}}{\mathrm{com\_ha}}$. |

---

## 3. Evidencia Empírica del Denominador `com_ha`

Se analizó la relación entre la superficie territorial DPA y el valor `com_ha` publicado por CONAF en diversas comunas extremas y centrales:

```text
1. Comuna de Diego de Almagro (Región de Atacama):
   - Superficie territorial DPA total: 1.866.490 ha (desierto mayoritario)
   - Valor com_ha publicado por CONAF: 21.550 ha (matorrales y vegetación riparia)
   - Ratio combustible / total: 1.15 %

2. Comuna de Colchane (Región de Tarapacá):
   - Superficie territorial DPA total: 401.560 ha (altiplano)
   - Valor com_ha publicado por CONAF: 177.125 ha (bofedales y tolares)
   - Ratio combustible / total: 44.11 %

3. Comunas de la Región Metropolitana (p. ej. San José de Maipo, Paine):
   - com_ha excluye glaciares, nieves perennes, roca desnuda y áreas urbanas consolidadas.
```

Además, todos los valores observados de `com_ha` son múltiplos de $25\ \mathrm{ha}$ ($500\ \mathrm{m} \times 500\ \mathrm{m}$), confirmando que la contabilidad zonal se ejecuta sobre una grilla espacial discretizada a $500\ \mathrm{m}$.

---

## 4. Reglas No Negociables para M0: Prohibición de Reglas Nuevas

1. **Sin Umbrales Semafóricos Artificiales:**  
   M0 **no debe clasificar a priori** las comunas en "Rojo" o "Amarillo" mediante porcentajes comunales como $\ge 30\%$ o $10\text{--}29\%$, salvo que exista documentación oficial que demuestre que CONAF utilizaba esa regla en el sistema legado.
2. **Salida Pura:**  
   M0 genera la tupla analítica exacta de CONAF:
   $$(\mathrm{date}, \mathrm{com\_id}, \mathrm{horas}, \mathrm{SUM\_br\_ha}, \mathrm{com\_ha}, \mathrm{proportion})$$
3. **Múltiples Filas por Comuna y Día:**  
   Una comuna puede tener varias filas en un mismo día (p. ej. una fila para `horas = 1`, otra para `horas = 2`, otra para `horas = 5`), exactamente como lo reporta el Feature Service oficial.
