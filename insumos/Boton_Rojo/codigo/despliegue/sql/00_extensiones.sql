-- Extensiones necesarias. Se ejecuta una sola vez, al inicializar el volumen.
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS postgis_raster;
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- pgstac se instala aparte, porque trae su propio migrador:
--   pypgstac migrate --dsn postgresql://usuario:clave@localhost:5432/botonrojo
