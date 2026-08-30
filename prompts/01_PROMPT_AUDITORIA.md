# Prompt de fase 0 — Auditoría

Ejecuta únicamente la Fase 0 del roadmap BR-HR.

Lee los dos insumos originales, calcula hashes y produce:

1. `docs/generated/00_INVENTARIO_INSUMOS.md`
2. `docs/generated/01_AUDITORIA_LEGACY.md`
3. `docs/generated/02_PERFIL_DATOS_INCENDIOS.md`
4. `docs/generated/03_GAPS_Y_RIESGOS.md`
5. `docs/generated/DECISION_LOG.md`
6. `PLAN_IMPLEMENTACION.md`

No hagas todavía una refactorización grande.

En la auditoría del legado verifica específicamente resolución efectiva, resampling, manejo horario, uso real de parámetros de escala, matriz PI, HCFM, exposición, combustible y arquitectura de publicación.

En el perfil de datos recalcula todas las cifras a partir del CSV real y separa hechos observados de supuestos.
