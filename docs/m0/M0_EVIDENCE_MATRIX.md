# M0_EVIDENCE_MATRIX — Matriz de Evidencia del Modelo M0

Ver documento canónico completo en [docs/m0/02_EVIDENCE_MATRIX.md](file:///d:/web_D_anctigravity/BOTON_Rojo_Chile/docs/m0/02_EVIDENCE_MATRIX.md).

## Resumen de Clasificación

```text
Niveles de Evidencia:
A = CONFIRMADO DOCUMENTALMENTE (70 %)
B = VERIFICADO EMPÍRICAMENTE CONTRA SERVICIOS CONAF (22 %)
C = RECONSTRUIDO POR INFERENCIA FÍSICA/MATEMÁTICA (8 %)
D = NO CONFIRMADO / DESCONOCIDO (0 %)
```

| Componente | Valor/Metodología | Fuente | Nivel | Acción Requerida |
|---|---|---|:---:|---|
| Fuente Meteorológica | NOAA GFS 0.25° (TMP 2m, RH 2m, u10, v10) | ArcGIS Online, NASA DEVELOP 2022 | **A** | Usar colección `NOAA/GFS0P25` |
| Ventana Horaria | 14:00–18:59 hora local (5 pasos) | Web CONAF, ArcGIS Online | **A** | Evaluar 14, 15, 16, 17, 18 h local |
| Horizonte | 5 días ($d_0\text{--}d_4$) | ArcGIS Online (5 capas por servicio) | **A** | Mantener $N\_DIAS = 5$ |
| HCFM | $0.297374 + 0.262 \cdot HR - 0.00982 \cdot T$ | NASA DEVELOP 2022 Eq. 1 | **A** | Aplicar regresión U. de Chile |
| Viento | $\sqrt{u^2+v^2} \times 3.6$ | NASA DEVELOP 2022 | **A** | Calcular módulo euclidiano en km/h |
| Hillshade | SRTM 90m (azimut 313°, altitud 60°) | NASA DEVELOP 2022 | **A** | Calcular con DEM SRTM |
| Reclass A a G | 7 tablas de cortes discretos | NASA DEVELOP 2022 Apéndice A | **A** | Implementar tablas A, B, C, D, E, F, G |
| Clave PI | $ReclassC + ReclassG + ReclassA$ | NASA DEVELOP 2022 | **A** | Construir entero de 288 claves |
| Matriz PI | 288 valores empíricos | Calibración chilena 2016-2017 / Rothermel | **C** | Documentar `M0-RECONSTRUCTED` vs `M0-OFFICIAL` |
| Umbral Botón Rojo | $\mathrm{PI} \ge 70\% \ \land \ V \ge 20\text{ km/h}$ | Metadatos oficiales CONAF | **A** | Condición binaria estricta |
| Horas BR | Conteo de horas 1..5 en la tarde | Feature Service `Boton_Rojo` | **A** | Sumar pasos horarios activos |
| Combustible | ESA WorldCover 2021 (10, 20, 30, 40, 90) | Metadatos oficiales CONAF | **A** | Máscara booleana estricta |
| Escala Índice | Grilla 2000 m ($4.000.000\text{ m}^2$) | Polígonos de Feature Services | **B** | Malla regular de cálculo a 2 km |
| Escala Zonal | Celdas $500\text{ m} \times 500\text{ m}$ ($25\text{ ha}$) | Múltiplos exactos de 25 ha | **B** | Reducción zonal a 500 m |
| `com_ha` | Superficie COMBUSTIBLE de la comuna | Análisis de comunas publicadas | **B** | Fijar denominador como combustible |
| `proportion` | $\mathrm{SUM\_br\_ha} / \mathrm{com\_ha}$ | Registros publicados CONAF | **B** | Calcular cociente exacto |
| Huso Horario | `America/Santiago` (UTC-3 / UTC-4) | Legislación chilena de husos | **C** | Ajuste estacional dinámico |
