# RESOLUCION_Y_ESCALAS_M0 — Escalas y Resolución del Botón Rojo Original

Ver documento canónico completo en [docs/m0/06_RESOLUCION_Y_ESCALAS.md](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/docs/m0/06_RESOLUCION_Y_ESCALAS.md).

## Resumen Ejecutivo

```text
┌─────────────────────────┬───────────────────┬────────────────────────────────────────┐
│ Nivel de Proceso        │ Escala Nominal    │ Naturaleza y Evidencia                 │
├─────────────────────────┼───────────────────┼────────────────────────────────────────┤
│ Insumo Meteorológico    │ ~25 km (0.25°)    │ GFS Nativo (NOAA/GFS0P25)              │
│ Malla del Índice        │ 2.000 m           │ Remuestreo bilineal (4.000.000 m²)     │
│ Contabilidad Zonal      │ 500 m (25 ha)     │ com_ha es múltiplo exacto de 25 ha     │
│ Máscara Combustible     │ 10 m -> 500 m     │ ESA WorldCover v200 clases 10,20,30,40,90│
└─────────────────────────┴───────────────────┴────────────────────────────────────────┘
```

### Reglas para la Implementación Fiel M0:
1. Resamplear únicamente campos meteorológicos continuos ($T, \mathrm{HR}, u, v$) a 2 km.
2. Calcular la física ($HCFM, \text{Viento}, \text{Clave}, PI, BR$) de forma discreta sobre la malla remuestreada.
3. Ejecutar la reducción zonal comunal (`reduceRegions`) a escala de 500 m sobre la máscara de combustible.
