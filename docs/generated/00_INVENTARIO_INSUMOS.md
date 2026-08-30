# 00 — Inventario de Insumos y Verificación Criptográfica

Fecha de generación: 29 de agosto de 2026  
Entorno: BR-HR — Fase 0 (Auditoría y Planificación)

---

## 1. Resumen de Insumos Originales

Los insumos originales se encuentran en el directorio de solo lectura `insumos/`. Se han verificado de manera no destructiva mediante hashing SHA-256 e inspección estructural directa.

| Insumo | Tamaño (bytes) | Formato | SHA-256 | Estado / Política |
|---|---|---|---|---|
| `insumos/Boton_Rojo.zip` | 713.178 | ZIP comprimido | `7b6c3b82815598df85a2bee8f1ff89915a5daa648e3340d64c2fa74a7a47a3da` | **Solo lectura inmutable** |
| `insumos/Consolidado_incendios_2014_2024_temporada.csv` | 49.872.706 | CSV delimitado por `;` (UTF-8) | `57a9e57e6d2dcfb845c73c1ddb88eb8f8d0c4ac765c4e8976ef270fb32d71286` | **Solo lectura inmutable** |

---

## 2. Inventario Detallado del Sistema Legado (`Boton_Rojo.zip`)

El archivo comprimido fue extraído hacia el espacio de trabajo derivado `work/legacy_boton_rojo/` sin alterar el archivo original. Contiene 24 archivos organizados de la siguiente manera:

```text
work/legacy_boton_rojo/Boton_Rojo/
├── Arquitectura_Boton_Rojo_Open_Source.html   (43.180 B)  — Blueprint de pila libre (TiTiler, pygeoapi, PostGIS, Martin, Grafana)
├── LEEME.md                                  (4.516 B)   — Documento de arranque institucional UIA/CONAF
├── UIA_Metodologia_Boton_Rojo_CONAF.docx     (526.055 B) — Informe metodológico completo (9 páginas)
├── UIA_Metodologia_Boton_Rojo_CONAF.pdf      (147.641 B) — Versión PDF del informe metodológico
├── matriz_probabilidad_ignicion.csv          (13.987 B)  — Matriz 288 celdas en formato plano
├── matriz_probabilidad_ignicion.xlsx         (25.310 B)  — Matriz en 4 hojas (base, expuesto, sombreado, variantes)
└── codigo/
    ├── README.md                             (6.158 B)   — Documentación técnica de código y comandos
    ├── requirements.txt                      (270 B)     — Dependencias Python de la réplica
    ├── nucleo.py                             (18.527 B)  — Algoritmo puro en NumPy (HCFM, Reclass A-G, PI, BR)
    ├── boton_rojo_gee.js                     (14.192 B)  — Réplica para Google Earth Engine (JavaScript)
    ├── pipeline.py                           (15.213 B)  — Pipeline ejecutable offline (NOMADS GFS -> Zonal Comunas)
    ├── conaf_api.py                          (14.804 B)  — Cliente ArcGIS REST (cosecha, capas TP/HR/HC/VV/PI/BR)
    ├── generar_matriz.py                     (4.196 B)   — Generador de matriz en CSV, Excel y JS
    ├── generar_informe.py                    (29.408 B)  — Generador de informe Word institucional
    ├── publicar.py                           (12.018 B)  — Conversor COG, catalogador STAC e ingestor PostGIS
    └── despliegue/
        ├── compose.yaml                      (5.025 B)   — Docker/Podman compose de servicios
        ├── env.ejemplo                       (335 B)     — Plantilla de variables de entorno
        ├── pygeoapi/
        │   └── local.config.yml              (4.569 B)   — Configuración OGC API Features/Coverages
        ├── sql/
        │   └── 00_extensiones.sql            (351 B)     — Script de extensiones PostgreSQL (postgis, pgstac)
        └── systemd/
            ├── INSTALAR.md                   (1.246 B)   — Guía de despliegue systemd
            ├── boton-rojo.target             (365 B)     — Target systemd
            ├── boton-rojo.timer              (528 B)     — Timer systemd diario
            ├── boton-rojo-descarga.service   (596 B)     — Servicio de descarga GFS
            ├── boton-rojo-calculo.service    (784 B)     — Servicio de cálculo zonal
            └── boton-rojo-publicacion.service(692 B)     — Servicio de publicación STAC/PostGIS
```

---

## 3. Inventario del Consolidado Histórico de Incendios

- **Archivo:** `Consolidado_incendios_2014_2024_temporada.csv`
- **Registros totales:** 68.546 filas (excluyendo cabecera)
- **Columnas totales:** 79 campos
- **Codificación detectada:** `UTF-8`
- **Separador:** Punto y coma (`;`)
- **Periodo temporal:** Temporadas 2014–2015 a 2023–2024 (10 temporadas completas)
- **Rango de fechas de inicio:** 2014-07-14 13:15:00 a 2024-06-28 16:10:00
- **Duplicados exactos de fila:** 0
- **Duplicados de índice (`index`):** 0

---

## 4. Trazabilidad y Reglas de Preservación

1. Los archivos en `insumos/` no se modifican, renombran ni sobrescriben bajo ninguna circunstancia.
2. Todo procesamiento posterior se ejecutará a partir de scripts reproducibles que lean desde `insumos/` y escriban datos derivados exclusivamente en:
   - `work/` (archivos intermedios de trabajo)
   - `data/derived/` (datasets maestros Parquet y geometrías procesadas)
   - `artifacts/` (modelos, métricas y reportes)
