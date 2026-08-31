# 00 — Inventario de Fuentes e Insumos Primarios del Botón Rojo M0

**Proyecto:** BR-HR — Botón Rojo de Alta Resolución  
**Componente:** Línea Base M0 (Botón Rojo Original CONAF/GEPRIF)  
**Fecha:** 30 de agosto de 2026  
**Responsables:** Senior Geospatial Architect, Fire Science Reviewer, Scientific Reproducibility Auditor  

---

## 1. Paquetes e Insumos Primarios

Los insumos originales de referencia se encuentran almacenados bajo la carpeta `insumos/` en modo **solo lectura**, habiéndose extraído una copia de trabajo íntegra e inalterada en `work/m0_original/`.

| Identificador | Archivo / Recurso | SHA-256 Checksum | Tamaño (bytes) | Estado / Naturaleza |
|---|---|---|---|---|
| **INS-01** | `insumos/Boton_Rojo.zip` | `7b6c3b82815598df85a2bee8f1ff89915a5daa648e3340d64c2fa74a7a47a3da` | 741.011 | Insumo primario original (ZIP comprimido) |
| **INS-02** | `insumos/Consolidado_incendios_2014_2024_temporada.csv` | *(Verificado en QA)* | 108.542.190 | Registro histórico oficial CONAF (10 temporadas) |
| **INS-03** | `work/m0_original/Boton_Rojo/` | *(Directorio de trabajo)* | — | Copia de trabajo exacta extraída |

---

## 2. Inventario de Documentos del Paquete M0

| Archivo | Formato | Tamaño | Descripción Técnica y Metodológica |
|---|---|---|---|
| `UIA_Metodologia_Boton_Rojo_CONAF.docx` | DOCX | 526.055 | Documento técnico maestro de la Unidad de Información y Análisis (UIA) de CONAF (27/08/2026). Detalla la formulación matemática, insumos GFS/SRTM/WorldCover, 7 tablas de reclasificación, matriz PI y reglas comunales. |
| `UIA_Metodologia_Boton_Rojo_CONAF.pdf` | PDF | 147.641 | Versión estática y congelada del informe institucional. |
| `Arquitectura_Boton_Rojo_Open_Source.html` | HTML | 43.180 | Documento de diseño arquitectónico open-source: mapeo de servicios GEE/ArcGIS a stack libre (PostGIS, STAC, TiTiler, pygeoapi, Martin). |
| `matriz_probabilidad_ignicion.xlsx` | XLSX | 25.310 | Matriz de 288 celdas en hojas: *Matriz 288 celdas*, *Expuesto*, *Sombreado* y *Variantes*. |
| `matriz_probabilidad_ignicion.csv` | CSV | 13.987 | Matriz de 288 celdas en formato relacional plano (clave, clave_hcfm, hcfm_pct, sombreado, clase_temperatura, temperatura_c, probabilidad_ignicion_pct, activa_umbral_70). |
| `LEEME.md` | Markdown | 4.516 | Resumen ejecutivo, advertencias operativas sobre la matriz no oficial y guía de uso rápido. |

---

## 3. Inventario de Código Fuente Heredado (`work/m0_original/Boton_Rojo/codigo/`)

| Archivo | Lenguaje / Entorno | Líneas | Función en la Cadena Metodológica |
|---|---|---|---|
| `nucleo.py` | Python 3 (NumPy) | 424 | Implementación matemática pura: fórmula HCFM U. de Chile, cálculo de viento euclidiano, hillshade SRTM, 7 funciones de reclasificación (Reclass A–G), generador de matriz Rothermel/BehavePlus, clave compuesta y regla binaria Botón Rojo ($PI \ge 70 \land V \ge 20$). Incluye 4 suites de verificación sintética. |
| `boton_rojo_gee.js` | JavaScript (Google Earth Engine) | 284 | Script ejecutable en GEE Code Editor. Procesa NOAA GFS 0.25°, SRTM 90 m, ESA WorldCover 2021, genera grilla horaria 14:00–18:59, acumula horas (1..5), filtra por máscara combustible y calcula estadística zonal comunal (`reduceRegions`). |
| `pipeline.py` | Python 3 (xarray, rasterio, geopandas) | 345 | Pipeline local fuera de GEE: descarga GRIB2 desde NOAA NOMADS, recorta a Chile, interpola a grilla regular de 2 km, calcula horas BR y realiza estadística zonal con polígonos comunales. |
| `conaf_api.py` | Python 3 (requests, pandas, geopandas) | 347 | Cliente REST para Feature Services de CONAF en ArcGIS Online (`services5.arcgis.com/A1ELWse9bRAi2JiV/`). Incluye consulta paginada, cosecha diaria idempotente y algoritmo de inversión empírica de la matriz PI (`calibrar_matriz`). |
| `generar_matriz.py` | Python 3 (pandas, openpyxl) | 106 | Script para generar y exportar la matriz reconstruida de 288 combinaciones en formatos XLSX, CSV y JS. |
| `generar_informe.py` | Python 3 (python-docx) | 385 | Script automatizado que genera el informe institucional DOCX formal. |
| `publicar.py` | Python 3 (rio-cogeo, pystac, psycopg) | 282 | Publicación de COG, catálogos STAC en pgstac y capas vectoriales comunales en PostGIS. |
| `despliegue/compose.yaml` | Podman/Docker Compose | 120 | Stack de microservicios: PostGIS + pgstac + TiTiler + pygeoapi + Martin + Grafana. |

---

## 4. Fuentes Externas e Institucionales de Referencia

1. **Metadatos Oficiales ArcGIS Online CONAF:**  
   - Ítem ID: `41ee3c691359437aa9df2a09d7f6124e`  
   - Propietario: `deigeprif` (Departamento de Desarrollo e Investigación, GEPRIF/CONAF).  
   - Endpoints REST: `https://services5.arcgis.com/A1ELWse9bRAi2JiV/arcgis/rest/services` (`TP`, `HR`, `HC`, `VV`, `PI`, `Boton_Rojo`).
2. **NASA DEVELOP Technical Report (2022):**  
   - *Chile Disasters: Automating Wildfire Risk and Occurrence Mapping in Google Earth Engine*  
   - Identificadores NASA: NTRS `20220005936` (Technical Paper) y `20220007384` (Code Tutorial / Software User Guide).  
   - Autores en colaboración directa con CONAF (GEPRIF).
3. **National Wildfire Coordinating Group (NWCG):**  
   - *Incident Response Pocket Guide (IRPG)* (PMS 461) — Tabla de *Probability of Ignition*.  
   - Algoritmo matemático: `ignite.cpp`, USDA Forest Service Rocky Mountain Research Station (Missoula Fire Sciences Laboratory, Rothermel 1983, Schroeder 1969).
4. **Catálogos de Satélites y Colecciones en Google Earth Engine:**  
   - Meteorología: `NOAA/GFS0P25` (Global Forecast System 0.25 Degree).  
   - Topografía: `CGIAR/SRTM90_V4` (SRTM 90m Digital Elevation Database v4).  
   - Cobertura de Suelo: `ESA/WorldCover/v200` (ESA WorldCover 10m 2021).  
   - División Administrativa: `SUBDERE / IGM / INE` (DPA 2023).
