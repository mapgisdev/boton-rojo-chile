# Réplica del Botón Rojo de CONAF

Reconstrucción ejecutable de la metodología del índice **Botón Rojo** de la
Gerencia de Protección contra Incendios Forestales (GEPRIF) de CONAF.

Unidad de Información y Análisis (UIA) — agosto de 2026.

---

## Qué es el Botón Rojo, en una línea

Una comuna queda en condición de Botón Rojo cuando, en el pronóstico GFS de NOAA
para la ventana **14:00–18:59** hora local, algún punto de su **superficie
combustible** presenta simultáneamente **probabilidad de ignición ≥ 70 %** y
**velocidad del viento ≥ 20 km/h**. Se publica a **5 días**.

## Cadena de cálculo

```
NOAA/GFS0P25  (T 2 m, HR 2 m, u10, v10)
   │
   ├─ HCFM = 0,297374 + 0,262·HR − 0,00982·T          → capa pública HC
   ├─ Viento = √(u² + v²) · 3,6                        → capa pública VV
   │
   ├─ clave = ReclassC(HCFM) + ReclassG(hillshade) + ReclassA(T)
   │            ‾‾‾‾‾‾‾‾‾‾‾‾   ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾    ‾‾‾‾‾‾‾‾‾‾‾
   │            2000…17000        100 ó 200               1…9
   │
   ├─ PI = MATRIZ[clave]                               → capa pública PI
   │
   ├─ Botón Rojo = (PI ≥ 70) ∧ (viento ≥ 20 km/h)      → RFW == 2
   ├─ horas = nº de pasos horarios (1…5) que cumplen
   ├─ máscara ESA WorldCover 2021: clases 10/20/30/40/90
   └─ zonal por comuna → SUM_br_ha, com_ha, proportion  → servicio Boton_Rojo
```

## Archivos

| Archivo | Qué hace |
|---|---|
| `nucleo.py` | Algoritmo puro en numpy: HCFM, reclasificaciones, matriz PI, regla de activación. Ejecutarlo corre cuatro verificaciones. |
| `generar_matriz.py` | Genera la matriz de 288 celdas en Excel, CSV y JavaScript. |
| `boton_rojo_gee.js` | Réplica en Google Earth Engine, el mismo entorno que usa CONAF. |
| `pipeline.py` | Réplica fuera de GEE: descarga GFS de NOMADS, calcula y agrega por comuna. |
| `conaf_api.py` | Cliente de los servicios REST de CONAF: descarga, cosecha diaria y calibración empírica de la matriz. |
| `publicar.py` | Publicación abierta: COG, ítems STAC en pgstac y tabla comunal en PostGIS. |
| `despliegue/` | Pila de servicios y unidades systemd para operar el índice sin plataformas propietarias. |
| `matriz_probabilidad_ignicion.xlsx` | Matriz reconstruida, en tres variantes comparables. |

## Automatización y publicación sin plataformas propietarias

`despliegue/` contiene lo necesario para operar el índice en un solo servidor
—8 núcleos, 32 GB de RAM y 1 TB NVMe bastan para el cálculo nacional a 2 km—
reemplazando Google Earth Engine por un cálculo propio y ArcGIS Online por
servicios abiertos.

```bash
cd despliegue
cp env.ejemplo .env          # completar claves y rutas
podman-compose up -d          # PostGIS, STAC, TiTiler, pygeoapi, Martin, Grafana

sudo cp systemd/boton-rojo-*.service systemd/boton-rojo.{target,timer} /etc/systemd/system/
sudo systemctl enable --now boton-rojo.timer
journalctl -u 'boton-rojo-*' -f
```

| Función | Servicio | Puerto local |
|---|---|---|
| Catálogo STAC | stac-fastapi-pgstac | 8081 |
| Teselas raster de los COG | TiTiler | 8082 |
| **OGC API Features y Coverages** | **pygeoapi** | **8083** |
| Teselas vectoriales de comunas | Martin | 8084 |
| Vigilancia operacional y alertas | Grafana | 8085 |
| Visor público | MapLibre GL JS sobre nginx | 8080 |

pygeoapi es la pieza que hoy no existe: publica el producto como OGC API, que es
la vía por la que la IDE de Chile y SENAPRED pueden consumirlo sin depender de un
tablero embebido. Todos los puertos se exponen solo en `127.0.0.1`; la salida a
internet debe pasar por un proxy inverso propio que resuelva TLS.

La orquestación son cinco unidades systemd encadenadas con `Requires=` y `After=`,
con reintentos, límites de CPU y memoria y registro en journalctl. Airflow 3 se
justifica más adelante, cuando el flujo se ramifique o lo opere más de una persona.

## Puesta en marcha

```bash
pip install requests numpy pandas openpyxl xarray cfgrib rasterio geopandas scipy

python nucleo.py                       # verificaciones del algoritmo
python generar_matriz.py               # matriz en xlsx / csv / js

python conaf_api.py br  --salida boton_rojo_vigente.xlsx     # producto oficial vigente
python conaf_api.py cosechar                                  # archiva la corrida del día
python pipeline.py --salida replica.xlsx                      # réplica propia
```

Para `pipeline.py` hay que proveer, una sola vez y en EPSG:4326:

- `dem.tif` — SRTM 90 m (CGIAR) o Copernicus DEM GLO-30
- `worldcover.tif` — ESA WorldCover v200 (2021), con los códigos originales
- `comunas.gpkg` — División Política Administrativa 2023 (SUBDERE / IGM / INE)

## Lo que está confirmado y lo que no

**Confirmado** por los metadatos oficiales del ítem ArcGIS Online de CONAF y por
la documentación de NASA DEVELOP elaborada con CONAF (NTRS 20220005936 y
20220007384): la fuente meteorológica, la ventana horaria, los dos umbrales, la
máscara de cobertura, la fórmula de HCFM, la de viento, el uso del hillshade y
las siete tablas de reclasificación.

**Verificado empíricamente** contra los servicios publicados: la grilla del
índice equivale a celdas de 2 km, `com_ha` corresponde a la superficie
*combustible* de la comuna y no a su superficie total, se contabiliza sobre
celdas de 500 m (25 ha), y el campo `horas` recorre 1 a 5.

**No publicado, y por tanto reconstruido**: la matriz de 288 valores que traduce
la clave compuesta a probabilidad de ignición. Aquí se genera con la ecuación de
Rothermel/BehavePlus, que reproduce la tabla NWCG con error medio de 0,83 puntos
porcentuales. CONAF, en cambio, la calibró con la temporada 2016-2017 chilena.
**Antes de cualquier uso operativo debe sustituirse por la matriz oficial** —
solicitándola a `dei.geprif@conaf.cl` — **o calibrarse** con
`conaf_api.calibrar_matriz()`.

## Cita

Los datos del Botón Rojo son de uso público; su utilización debe citar a CONAF
como fuente (Departamento de Desarrollo e Investigación, GEPRIF).
