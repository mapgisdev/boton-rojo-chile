# 07 — Arquitectura Earth Engine

## Objetivo

Mantener lógica modular, testeable conceptualmente y separada entre baseline e innovación.

## Módulos propuestos

```text
gee/
├── config/
│   └── defaults
├── meteorology/
│   ├── era5_land
│   ├── gfs
│   └── transforms
├── terrain/
│   ├── dem
│   ├── slope_aspect
│   ├── tpi
│   └── solar_exposure
├── fuels/
│   ├── mapbiomas
│   ├── fuel_fractions
│   └── dynamic_state
├── baseline/
│   ├── hcfm
│   ├── pi_matrix
│   └── boton_rojo
├── downscaling/
│   ├── temperature
│   ├── humidity
│   └── wind
├── inference/
│   ├── logistic
│   ├── rf
│   └── confidence
├── h3/
│   ├── aggregation
│   └── commune_rollup
└── publishing/
    ├── map_tiles
    └── exports
```

## Baseline

No mezclar funciones del baseline con BR-HR mejorado.

Crear test vectors para:
- HCFM;
- clases;
- PI;
- threshold;
- ventana horaria.

## Escala

La escala analítica debe ser explícita.

No asumir que:
```js
var ESCALA_INDICE = 2000;
```
produce automáticamente un raster de 2 km.

Verificar proyección, escala y reducer.

## Resampling

Separar por tipo:

### Continuo
- temperatura;
- dew point/humidity continuous fields;
- viento, con cautela.

### Categórico
- fuel class;
- flags;
- BR.

No aplicar bilinear a un stack mixto con flags.

## H3

No asumir `reduceRegions` masivo como única solución.

Benchmark estrategias y documentar.

## Export/publishing

Para live map:
- map tiles / Earth Engine REST.

Para histórico:
- tablas por H3;
- Parquet/JSON vía pipeline;
- rasters COG cuando tengan valor real.

No generar enormes exports diarios si los tiles y atributos agregados son suficientes.
