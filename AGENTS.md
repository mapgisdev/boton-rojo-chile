# Agentes sugeridos para BR-HR

El agente principal debe coordinar las siguientes responsabilidades conceptuales. Pueden implementarse como subagentes si el entorno lo permite.

## Geospatial Architect
Responsable de Earth Engine, H3, raster/vector, escalas, tiles, PMTiles, R2 y publicación.

## Fire Science / Methodology Reviewer
Responsable de preservar la lógica Botón Rojo, revisar HCFM/PI, exposición, combustible y evitar cambios científicamente injustificados.

## Data Scientist
Responsable de case-control, leakage, calibración, cross-validation temporal/espacial, modelos y métricas.

## Data Engineer
Responsable de QA/QC, esquema MASTER_FIRE_H3, Parquet, lineage y reproducibilidad.

## Backend Engineer
Responsable de Railway API, autenticación Earth Engine, cache y contratos.

## Frontend / GeoLibre Integrator
Responsable de mapas, consultas H3, capas, leyendas, performance y UX de riesgo.

## QA Engineer
Responsable de tests unitarios, regresión del baseline, test de contratos, pruebas de integración y criterios de aceptación.

El agente principal debe evitar que un subagente optimice su componente rompiendo los principios metodológicos globales.
