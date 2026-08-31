# DECISION_LOG — Registro de Decisiones Metodológicas y Forenses de M0

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Componente:** Bitácora de Decisiones Científicas y Técnicas M0  
**Fecha:** 30 de agosto de 2026  

---

### M0-DEC-001: Aislamiento Metodológico Estricto de M0 frente a BR-HR
- **Fecha:** 2026-08-30
- **Pregunta:** ¿Deben compartirse componentes algorítmicos o mejoras de BR-HR dentro de M0?
- **Evidencia:** Requerimiento científico fundamental de control experimental. Toda mejora en M0 falsearía la medición del valor agregado real de BR-HR.
- **Alternativas:**
  1. *Alternativa A:* Integrar mejoras en HCFM o combustible en M0.
  2. *Alternativa B (Seleccionada):* Mantener M0 como réplica 100 % fiel y congelada del sistema original CONAF, sin H3, sin ML y sin nuevas reglas.
- **Decisión:** Implementar y congelar M0 de forma totalmente desacoplada de BR-HR.
- **Nivel de Confianza:** Alta (100 %)
- **Impacto:** Garantiza validez científica y reproducibilidad del baseline experimental.

---

### M0-DEC-002: Fijación del Horizonte de Pronóstico en 5 Días ($d_0\text{--}d_4$)
- **Fecha:** 2026-08-30
- **Pregunta:** ¿Debe M0 procesar 3 o 5 días de pronóstico?
- **Evidencia:** Los Feature Services de CONAF en ArcGIS Online contienen exactamente 5 capas (`d0` a `d4`), los metadatos institucionales señalan "cinco días", y los scripts operacionales procesan 120 horas de pronóstico GFS.
- **Alternativas:**
  1. *Alternativa A:* Restringir a 3 días (versión prototípica de 2018).
  2. *Alternativa B (Seleccionada):* Fijar en 5 días ($d_0\text{--}d_4$), correspondiente al sistema operativo vigente 2023–2026.
- **Decisión:** M0 procesará un horizonte de 5 días ($N\_DIAS = 5$).
- **Nivel de Confianza:** Alta (100 %)
- **Impacto:** Concordancia exacta con el servicio operacional publicado por CONAF.

---

### M0-DEC-003: Definición del Denominador Comunal `com_ha`
- **Fecha:** 2026-08-30
- **Pregunta:** ¿El campo `com_ha` corresponde a la superficie total de la comuna o a su superficie combustible?
- **Evidencia:** Interrogación empírica de 14 comunas en el Feature Service oficial demostró que `com_ha` coincide con la suma de celdas de combustible (ESA WorldCover 10, 20, 30, 40, 90) cuantizadas a 25 ha, y no con el área administrativa de la DPA.
- **Alternativas:**
  1. *Alternativa A:* Usar superficie administrativa total.
  2. *Alternativa B (Seleccionada):* Usar superficie combustible de la comuna como denominador de `proportion`.
- **Decisión:** `com_ha` es la superficie combustible comunal; $\mathrm{proportion} = \mathrm{SUM\_br\_ha} / \mathrm{com\_ha}$.
- **Nivel de Confianza:** Alta (100 %)
- **Impacto:** Replicación numérica exacta de los ratios publicados por CONAF.

---

### M0-DEC-004: Taxonomía y Gestión de la Matriz de Probabilidad de Ignición
- **Fecha:** 2026-08-30
- **Pregunta:** ¿Cómo reportar la matriz PI si CONAF no publica los 288 coeficientes exactos?
- **Evidencia:** NASA DEVELOP (2022) indica que CONAF calibró la matriz con la temporada 2016–2017 chilena. La matriz de Rothermel/BehavePlus es una reconstrucción teórica conservadora.
- **Alternativas:**
  1. *Alternativa A:* Asumir que la matriz de Rothermel es la oficial de CONAF.
  2. *Alternativa B (Seleccionada):* Mantener explícitamente tres variantes: `M0-OFFICIAL`, `M0-RECONSTRUCTED` (default física) y `M0-CALIBRATED-RECONSTRUCTION` (inversión empírica).
- **Decisión:** Clasificar transparentemente la matriz como reconstrucción física [C] y ofrecer inversión empírica contra capas operacionales de CONAF.
- **Nivel de Confianza:** Alta (100 %)
- **Impacto:** Honestidad académica y transparencia total sobre la incertidumbre de calibración.

---

### M0-DEC-005: Eliminación de Resampling Bilineal sobre Capas Categóricas en GEE
- **Fecha:** 2026-08-30
- **Pregunta:** ¿Cómo corregir el defecto de interpolación detectado en `boton_rojo_gee.js`?
- **Evidencia:** La línea 192 de `boton_rojo_gee.js` aplicaba `.resample('bilinear')` a capas booleanas (`BR`, `RFW`), generando flotantes espurios en los límites de decisión.
- **Alternativas:**
  1. *Alternativa A:* Mantener el error de implementación del script legado.
  2. *Alternativa B (Seleccionada):* Resamplear bilinealmente solo los inputs meteorológicos continuos ($T, \mathrm{HR}, u, v$) y ejecutar la lógica booleana de forma discreta sobre la grilla ya remuestreada.
- **Decisión:** Aplicar el remuestreo únicamente a variables meteorológicas continuas antes de las reclasificaciones.
- **Nivel de Confianza:** Alta (100 %)
- **Impacto:** Estabilidad numérica e integridad booleana estricta de las salidas.

---

### M0-DEC-006: Tratamiento Dinámico del Huso Horario en Chile (`America/Santiago`)
- **Fecha:** 2026-08-30
- **Pregunta:** ¿Cómo gestionar el desfase UTC estacional de Chile en M0?
- **Evidencia:** El script legado fijaba `DESFASE_UTC = -4` de forma estática. Chile opera en UTC-3 durante la temporada de incendios de verano (septiembre a abril).
- **Alternativas:**
  1. *Alternativa A:* Mantener UTC-4 fijo (desfase de 1 hora en verano).
  2. *Alternativa B (Seleccionada):* Implementar ajuste estacional conforme al Decreto Supremo 224/2022 (UTC-3 en verano, UTC-4 en invierno).
- **Decisión:** Ajustar dinámicamente la ventana 14:00–18:59 local según la fecha del año.
- **Nivel de Confianza:** Alta (100 %)
- **Impacto:** Evaluación en la verdadera hora de máxima insolación y temperatura vespertina.
