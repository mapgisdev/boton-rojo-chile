# 03 — Blueprint técnico

## Arquitectura MVP

```text
                            ┌─────────────────┐
                            │   Fuentes EO    │
                            │ ERA5/GFS/LULC   │
                            │ DEM/vegetación  │
                            └────────┬────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │ Google Earth Engine │
                          │ features / modelos  │
                          │ raster / H3/comuna  │
                          └─────────┬───────────┘
                                    │ REST
                      ┌─────────────┴──────────────┐
                      ▼                            ▼
                ┌──────────┐                ┌────────────┐
                │ Railway  │                │ Cloudflare │
                │ API      │                │ R2         │
                └────┬─────┘                └─────┬──────┘
                     │                            │
                     └──────────────┬─────────────┘
                                    ▼
                               ┌─────────┐
                               │GeoLibre │
                               └────┬────┘
                                    ▼
                         Pages / Workers Static
```

## Componentes

### Earth Engine
Responsabilidades:
- lectura de datasets;
- cálculo de variables;
- baseline;
- inferencia modelo operacional;
- raster ambiental;
- estadísticas H3/comuna;
- mapas/tiles.

### Python científico
Responsabilidades:
- QA/QC;
- H3 estático;
- controles;
- master dataset;
- training;
- calibration;
- validation;
- backtesting;
- reports.

No tiene que estar en la ruta request→map.

### Railway
Backend ligero:
- autenticación;
- tokens/credenciales server-side;
- Earth Engine REST;
- metadata de runs;
- consultas por H3/comuna;
- health;
- caché pequeña.

### R2
- PMTiles estáticos;
- Parquet de runs;
- JSON de comuna;
- model cards;
- métricas;
- históricos.

### GeoLibre
- visualización;
- selección H3;
- comparación capas;
- serie temporal;
- leyendas y confianza.

### PostGIS
No incluir por defecto.
ADR futuro si aparece una necesidad real.

## Estructura de repositorio sugerida

```text
src/
├── baseline/
│   ├── conaf_core.py
│   └── ...
├── training/
│   ├── qa/
│   ├── sampling/
│   ├── features/
│   ├── models/
│   └── validation/
├── gee/
│   ├── config/
│   ├── meteorology/
│   ├── terrain/
│   ├── fuels/
│   ├── baseline/
│   ├── downscaling/
│   ├── inference/
│   ├── h3/
│   └── publishing/
├── api/
│   ├── routers/
│   ├── services/
│   └── schemas/
├── publishing/
└── shared/
tests/
infra/
data/
├── derived/
└── schemas/
work/
artifacts/
docs/generated/
```

## Performance

No asumir que un `reduceRegions` nacional sobre todos los H3 será óptimo.

Benchmark:
1. reduceRegions directo;
2. partición por región/tile;
3. export batches;
4. rasterización de IDs/grupo si resulta viable;
5. simplificación de geometrías donde no afecte resultados.

Documentar tiempos/costes relativos y cuotas.

## Serving

- vista nacional: Earth Engine tiles;
- H3 geometry: PMTiles/R2;
- atributos dinámicos: API o Parquet/JSON particionado;
- histórico: R2.

Evitar duplicar geometría en cada run.
