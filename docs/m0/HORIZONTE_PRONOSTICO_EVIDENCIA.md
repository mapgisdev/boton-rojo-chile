# HORIZONTE_PRONOSTICO_EVIDENCIA — Evidencia del Horizonte Temporal M0

Ver documento canónico completo en [docs/m0/07_HORIZONTE_PRONOSTICO.md](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/docs/m0/07_HORIZONTE_PRONOSTICO.md).

## Dictamen Metodológico

- **Pregunta:** ¿El Botón Rojo M0 debe procesar 3 o 5 días de pronóstico?
- **Evidencia Empírica y Documental:**
  - Feature Services oficiales de CONAF en ArcGIS Online contienen exactamente 5 capas: `d0`, `d1`, `d2`, `d3`, `d4`.
  - Metadatos oficiales de CONAF establecen explícitamente: *"Su horizonte es de cinco días..."*
  - Scripts operacionales en GEE y Python definen `N_DIAS = 5` y `DIAS_PRONOSTICO = 5`.
- **Decisión Congelada:** M0 procesará formalmente **5 días de pronóstico ($d_0\text{--}d_4$)**.
