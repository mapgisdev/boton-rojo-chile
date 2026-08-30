# Insumos que debes colocar aquí

Copiar sin modificar:

```text
Boton_Rojo.zip
Consolidado_incendios_2014_2024_temporada(1).csv
```

## Reglas

- Estos archivos son originales de referencia.
- No editarlos.
- No sobrescribirlos.
- No extraer el ZIP dentro de `insumos/`.
- Antigravity debe extraerlo a `work/legacy_boton_rojo/`.
- Toda limpieza del CSV debe producir un archivo nuevo en `data/derived/`.

## Comprobaciones iniciales esperadas

Para el ZIP:
- inventario de contenido;
- checksums;
- versiones/dependencias;
- lectura de metodología;
- análisis de scripts.

Para el CSV:
- detección de encoding y separador;
- dimensiones;
- campos;
- nulos;
- duplicados;
- QA coordenadas;
- QA timestamps;
- QA meteorología;
- QA combustible;
- QA superficies;
- distribución temporal/espacial;
- diccionario de variables.

Registrar SHA-256 de ambos originales.
