# 09 — Protocolo y Métricas de Validación de Fidelidad M0 vs CONAF Oficial

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Componente:** Marco Metodológico de Validación del Baseline M0  
**Fecha:** 30 de agosto de 2026  
**Responsables:** QA Engineer, Scientific Reproducibility Auditor, Data Scientist  

---

## 1. Principio Fundamental de la Evaluación M0

La validación del modelo M0 **NO evalúa si predice mejor la ocurrencia o propagación de incendios**.

Su único objetivo científico es responder:
> **¿Con qué grado de fidelidad numérica y espacial reproduce M0 el producto que CONAF publica oficialmente?**

Cualquier optimización predictiva pertenece a BR-HR, no a M0. M0 debe actuar como un clon metodológico inalterado.

---

## 2. Métricas de Fidelidad Numérica y Espacial

| Métrica | Definición Matemática | Criterio de Aceptación para Alta Fidelidad |
|---|---|:---:|
| **MAE `com_ha`** | $\frac{1}{N}\sum \| \mathrm{com\_ha}_{\mathrm{M0}} - \mathrm{com\_ha}_{\mathrm{CONAF}} \|$ | $\le 25.0\ \mathrm{ha}$ (un píxel de 500 m) |
| **MAE `SUM_br_ha`** | $\frac{1}{N}\sum \| \mathrm{SUM\_br\_ha}_{\mathrm{M0}} - \mathrm{SUM\_br\_ha}_{\mathrm{CONAF}} \|$ | $\le 100.0\ \mathrm{ha}$ |
| **MAE `proportion`** | $\frac{1}{N}\sum \| \mathrm{prop}_{\mathrm{M0}} - \mathrm{prop}_{\mathrm{CONAF}} \|$ | $\le 0.05$ ($5\%$) |
| **Correlación de Pearson ($r$)** | $\mathrm{corr}(\mathrm{prop}_{\mathrm{M0}}, \mathrm{prop}_{\mathrm{CONAF}})$ | $r \ge 0.95$ |
| **Coincidencia Comunal ($F_1$)** | $F_1 = \frac{2 \cdot TP}{2 \cdot TP + FP + FN}$ (Presencia de comuna activa) | $F_1 \ge 0.90$ |
| **Coincidencia por Horas** | $\%$ de celdas con exactamente la misma clase de horas ($1\dots 5$) | $\ge 85\%$ |
| **IoU Espacial (Raster)** | $\mathrm{IoU} = \frac{\mathrm{Area}(\mathrm{BR}_{\mathrm{M0}} \cap \mathrm{BR}_{\mathrm{CONAF}})}{\mathrm{Area}(\mathrm{BR}_{\mathrm{M0}} \cup \mathrm{BR}_{\mathrm{CONAF}})}$ | $\mathrm{IoU} \ge 0.80$ |

---

## 3. Escenarios de Prueba Obligatorios

La suite de validación cruzada debe incluir al menos cuatro tipologías de eventos meteorológicos:

1. **Episodio Extremo de Olas de Calor de Verano:**  
   - Días con Botón Rojo generalizado en la zona central y sur (Regiones de Valparaíso a La Araucanía).
   - Comprobación de activación de 4 y 5 horas críticas continuas.
2. **Escenario de Riesgo Nulo / Invierno:**  
   - Días lluviosos o invernales con temperaturas bajas y humedades relativas sobre 70 %.
   - Comprobación de que M0 no emita falsas activaciones (salida vacía o 0 celdas activas).
3. **Escenario de Viento Intenso sin Ignición:**  
   - Días con frentes de viento costero ($V > 30\ \mathrm{km/h}$) pero con alta humedad ($HR > 60\% \implies \mathrm{PI} < 30\%$).
   - Comprobación del bloqueo estricto por la conjunción booleana ($PI \ge 70 \land V \ge 20$).
4. **Escenario de Altiplano / Zona Norte:**  
   - Comprobación de la máscara de combustible en zonas desérticas y bofedales (Regiones de Arica y Parinacota, Tarapacá, Antofagasta).

---

## 4. Escala de Madurez de la Réplica M0

```text
Nivel 1: RECONSTRUCCIÓN PARCIAL
- Cadena implementada en código pero con discrepancias en insumos, proyecciones o fórmulas.

Nivel 2: RÉPLICA FUNCIONAL
- Pipeline completo operativo de extremo a extremo.
- Insumos correctos (GFS, SRTM, WorldCover).
- Salida comunal estructurada, pero con matriz teórica Rothermel no calibrada.

Nivel 3: RÉPLICA VALIDADA
- Verificación cruzada exitosa frente a corridas cosechadas de CONAF.
- Coincidencia de com_ha en > 95 % de comunas y correlación r > 0.85 en días concurrentes.

Nivel 4: RÉPLICA DE ALTA FIDELIDAD (BASELINE CONGELADO)
- Matriz PI calibrada o suministrada por CONAF.
- Concordancia espacial IoU > 0.80 y F1 comunal > 0.90.
- Código congelado formalmente como M0 v1.0.0 sin modificaciones posteriores.
```
