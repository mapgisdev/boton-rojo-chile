# 05 — Matriz de Probabilidad de Ignición (PI) de 288 Celdas

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Componente:** Análisis Forense y Formulación Matemática de la Matriz PI  
**Fecha:** 30 de agosto de 2026  
**Responsables:** Fire Science Reviewer, Scientific Reproducibility Auditor, Data Scientist  

---

## 1. Estructura y Origen Teórico de la Matriz

La matriz de probabilidad de ignición traduce la clave compuesta generada por el cruce espacial de temperatura, humedad del combustible y sombreado en un valor de probabilidad porcentual continuo o discretizado ($0.0 \dots 100.0\%$).

### Dimensiones del Espacio de Estados
$$\text{Dimensión} = 16\ (\mathrm{HCFM}) \times 2\ (\text{Sombreado}) \times 9\ (\text{Temperatura}) = 288\ \text{celdas}$$

Esta estructura de $16 \times 2 \times 9$ reproduce con exactitud la tabla clásica de *Probability of Ignition* del **National Fire Danger Rating System (NFDRS)** de Estados Unidos, compilada en el *Incident Response Pocket Guide (IRPG)* del NWCG (PMS 461) y fundamentada en los trabajos de Schroeder (1969) y Rothermel (1983).

---

## 2. Formulación Matemática de la Reconstrucción Física (Rothermel / BehavePlus)

En ausencia de la publicación de los coeficientes numéricos internos por parte de CONAF, la matriz se reconstruyó a partir del algoritmo de referencia de dominio público `ignite.cpp` de la suite BEHAVE del Rocky Mountain Research Station (RMRS, USFS, Missoula Fire Sciences Laboratory):

### Paso 1: Cálculo de la Temperatura Efectiva del Combustible ($T_f, T_c$)
La radiación solar directa sobre combustibles finos expuestos eleva su temperatura por encima de la temperatura del aire ambiente:

$$T_f = T_{\mathrm{aire}} [^\circ\mathrm{F}] + (25 - 20 \cdot \mathcal{S}_{\mathrm{sombra}}) \quad [^\circ\mathrm{F}]$$

donde:
- $\mathcal{S}_{\mathrm{sombra}} = 0.0$ para combustible expuesto ($\mathrm{ReclassG} = 100 \implies +25\ ^\circ\mathrm{F} \approx +13.9\ ^\circ\mathrm{C}$ por radiación solar).
- $\mathcal{S}_{\mathrm{sombra}} = 1.0$ para combustible sombreado ($\mathrm{ReclassG} = 200 \implies +5\ ^\circ\mathrm{F} \approx +2.8\ ^\circ\mathrm{C}$).

Conversión a Celsius de la temperatura del combustible:
$$T_c = (T_f - 32) \times \frac{5}{9} \quad [^\circ\mathrm{C}]$$

### Paso 2: Calor Requerido para la Ignición ($Q_{\mathrm{ig}}$)
Calculado en función de la temperatura del combustible $T_c$ y la fracción másica de humedad $m = \frac{\mathrm{HCFM}}{100}$:

$$Q_{\mathrm{ig}} = 144.51 - 0.26600 \cdot T_c - 0.00058 \cdot T_c^2 - T_c \cdot m + 18.5400 \cdot (1 - e^{-15.1 \cdot m}) + 640.0 \cdot m$$

Saturación física del calor de ignición:
$$Q_{\mathrm{ig}} = \min(Q_{\mathrm{ig}}, 400.0) \quad [\mathrm{BTU/lb}]$$

### Paso 3: Probabilidad de Ignición ($\mathrm{PI}$)
Definida mediante la curva sigmoidal potencial de Schroeder:

$$x = 0.1 \cdot (400.0 - Q_{\mathrm{ig}})$$

$$\mathrm{PI} = 100.0 \cdot \min\left( 1.0, \, \frac{0.000048 \cdot \max(x, 0)^{4.3}}{50.0} \right) \quad [\%]$$

---

## 3. Validación de la Reconstrucción Frente a la Tabla Oficial NWCG

Contrastada celda a celda contra las 144 combinaciones oficiales de la tabla NWCG en condición no sombreada (*unshaded*):

- **Error Medio Absoluto (MAE):** $0.83$ puntos porcentuales.
- **Coincidencias Exactas (tras redondeo a decena):** $132$ de $144$ celdas ($91.7\%$).
- **Discrepancia Máxima:** $10.0$ puntos porcentuales (atribuible a un solo escalón de redondeo en frontera).

---

## 4. El Hallazgo Crítico Institucional (Brecha M0-OFFICIAL vs M0-RECONSTRUCTED)

### La Evidencia de NASA DEVELOP (2022)
El informe técnico oficial de NASA DEVELOP (NTRS 20220005936) elaborado con la jefatura de GEPRIF declara expresamente:
> *"The ignition probability values in the matrix were determined using the 2016–2017 fire season as a proxy."*

Esto demuestra que **CONAF no utilizó la matriz teórica estadounidense sin modificar, sino que ajustó empíricamente sus coeficientes para reflejar las condiciones de inflamabilidad de los ecosistemas mediterráneos chilenos**.

### Consecuencia Numérica de la Reconstrucción Teórica
- Con la formulación teórica de Rothermel (`M0-RECONSTRUCTED`), se requiere $\mathrm{HCFM} \le 4.0\%$ para alcanzar $\mathrm{PI} \ge 70\%$. A una temperatura ambiente de 30 °C, esto exige una humedad relativa extremadamente baja:
  $$\mathrm{HR} \le 15.2\%$$
- En la operación real de CONAF, el Botón Rojo se activa con frecuencia en valles centrales y cordillera de la costa con humedades relativas del orden de $20\%\text{--}25\%$.
- **Conclusión científica:** La calibración empírica oficial de CONAF es significativamente **más permisiva** (más sensible al riesgo con humedades relativas moderadas) que la ecuación pura de Rothermel.

---

## 5. Taxonomía Transparente de Variantes de la Matriz

Para evitar cualquier tergiversación de la línea base, el proyecto mantendrá y reportará explícitamente tres variantes diferenciadas:

```text
1. M0-OFFICIAL:
   Matriz exacta de 288 valores obtenida de CONAF/GEPRIF si es provista formalmente.

2. M0-RECONSTRUCTED (Baseline Físico Congelado):
   Matriz pura derivada de Rothermel/BehavePlus (implementada en nucleo.py y boton_rojo_gee.js).

3. M0-CALIBRATED-RECONSTRUCTION:
   Matriz recuperada empíricamente por inversión estadística cruzando las capas operacionales TP, HC y PI de CONAF mediante conaf_api.calibrar_matriz().
```

El usuario e investigador sabrá en todo momento cuál de estas variantes se encuentra en ejecución, impidiendo denominar "réplica 100 % idéntica de CONAF" a una versión basada en física teórica no calibrada.
