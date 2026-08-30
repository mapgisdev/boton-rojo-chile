# BR-HR — Contexto persistente del proyecto

@./docs/01_VISION_Y_ALCANCE.md
@./docs/02_METODOLOGIA_CIENTIFICA.md
@./docs/03_BLUEPRINT_TECNICO.md
@./docs/04_DATASET_MAESTRO.md
@./docs/05_PLAN_DE_DESARROLLO.md
@./docs/09_DECISIONES_NO_NEGOCIABLES.md

## Resumen operativo

Este repositorio desarrolla **BR-HR — Botón Rojo de Alta Resolución**.

### Objetivo
Preservar el Botón Rojo original como baseline y desarrollar una versión calibrada/probabilística con salida H3 subcomunal y agregación a comuna.

### Stack objetivo del MVP
- Google Earth Engine: motor geoespacial.
- Python: QA/QC, modelado, calibración, validación y tooling; no necesariamente en cada request.
- H3 resolución 8: unidad operacional.
- Railway: backend/API ligera y autenticación.
- Cloudflare R2: histórico, PMTiles, Parquet y JSON.
- GeoLibre: interfaz.
- Cloudflare Pages o Workers: hosting frontend.
- PostgreSQL/PostGIS: NO obligatorio en MVP.

### Insumos de solo lectura
- `insumos/Boton_Rojo.zip`
- `insumos/Consolidado_incendios_2014_2024_temporada(1).csv`

### Reglas clave
1. No alterar los insumos.
2. Auditar y congelar el baseline antes de refactorizarlo.
3. No confundir resampling con resolución efectiva.
4. No introducir data leakage.
5. Mantener test temporal ciego 2022–2024.
6. Calibrar probabilidades teniendo en cuenta el muestreo caso-control.
7. No hardcodear secretos.
8. Toda mejora debe demostrar ganancia cuantitativa.
9. Priorizar modelos operables e interpretables.
10. Documentar decisiones y versionar datos/modelos/corridas.

## Primer milestone
Auditoría completa + `PLAN_IMPLEMENTACION.md`.
