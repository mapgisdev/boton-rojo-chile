# Registro de Decisiones de Arquitectura y Metodología (DECISION_LOG)

Este registro documenta todas las decisiones arquitectónicas, metodológicas y supuestos adoptados durante el desarrollo de **BR-HR**.

---

### DEC-001: Inmutabilidad estricta del directorio `insumos/`
- **Fecha:** 2026-08-29
- **Estado:** Aprobada / En vigor
- **Contexto:** El usuario provee insumos de referencia (`Boton_Rojo.zip` y `Consolidado_incendios_2014_2024_temporada.csv`).
- **Decisión:** `insumos/` se declara de solo lectura. Todo script debe leer sin modificar in-place. Los datos derivados se escriben en `data/derived/`, el código legado en `work/legacy_boton_rojo/` y los modelos/reportes en `artifacts/`.
- **Consecuencias:** Trazabilidad y reproducibilidad garantizadas desde el origen.

---

### DEC-002: Partición Temporal Estricta (Blind Test 2022–2024)
- **Fecha:** 2026-08-29
- **Estado:** Aprobada / En vigor
- **Contexto:** Necesidad de prevenir sobreajuste temporal y evaluar generalización retrospectiva en eventos críticos (temporadas 2022-23 y 2023-24).
- **Decisión:**
  - **TRAIN:** Temporadas 2014–15 a 2020–21 (48.659 incendios, 70,99 %).
  - **VALIDATION:** Temporada 2021–22 (6.947 incendios, 10,13 %).
  - **TEST CIEGO:** Temporadas 2022–23 y 2023–24 (12.940 incendios, 18,88 %).
- **Consecuencias:** El conjunto de test ciego no puede ser utilizado para selección de variables, búsqueda de hiperparámetros ni calibración. Se evalúa una sola vez al finalizar el desarrollo.

---

### DEC-003: Definición de Dos Universos Temporales de Modelado
- **Fecha:** 2026-08-29
- **Estado:** Aprobada / En vigor
- **Contexto:** El Botón Rojo original evalúa únicamente la ventana de tarde (14:00–18:59), que concentra el 52,44 % de los incendios, mientras que el 47,56 % restante ocurre en otros horarios.
- **Decisión:**
  1. `BR-Window`: H3 $\times$ fecha $\times$ hora en ventana 14:00–18:59 para auditar y validar directamente la regla Botón Rojo (M0 y M1).
  2. `Ignition-24h`: H3 $\times$ fecha $\times$ hora (00:00–23:59) para el modelo probabilístico continuo $P(\mathrm{IGN})$ (M2).
- **Consecuencias:** No se descarta ningún incendio del histórico y se preserva la comparabilidad con la regla CONAF.

---

### DEC-004: Adopción de H3 Resolución 8 como Unidad Operacional Estándar
- **Fecha:** 2026-08-29
- **Estado:** Aprobada / En vigor
- **Contexto:** Necesidad de superar la granularidad comunal sin caer en falsa precisión micrometeorológica.
- **Decisión:** H3 resolución 8 (área promedio $\approx 73,7\ \mathrm{ha}$, radio $\approx 461\ \mathrm{m}$) es la unidad operacional base. H3 resolución 9 ($\approx 10,5\ \mathrm{ha}$) se mantiene como piloto experimental.
- **Consecuencias:** Los hexágonos mantienen identidad global inmutable; la agregación a comuna se realiza mediante una tabla de intersección de pesos espaciales (`h3_commune_weights`), sin cortar geometrías hexagonales.

---

### DEC-005: Exclusión de PostgreSQL/PostGIS del MVP
- **Fecha:** 2026-08-29
- **Estado:** Aprobada / En vigor
- **Contexto:** El sistema legado proponía una pila con PostGIS, pgstac, pygeoapi, Martin y TiTiler.
- **Decisión:** PostGIS no se incluye en el MVP. El almacenamiento de geometrías estáticas se realiza en PMTiles sobre Cloudflare R2, las series temporales y runs en Parquet/JSON sobre R2, y la orquestación/autenticación en una API stateless ligera en Railway.
- **Consecuencias:** Reducción drástica de costos, latencia y complejidad operativa.

---

### DEC-006: Tratamiento Explícito de Zonas Horarias IANA
- **Fecha:** 2026-08-29
- **Estado:** Aprobada / En vigor
- **Contexto:** El script legado fijaba `DESFASE_UTC = -4`, generando un descalce horario durante el horario de verano (UTC-3).
- **Decisión:** Estandarizar todo el pipeline utilizando la zona horaria IANA `America/Santiago` (y `Pacific/Easter` para Rapa Nui cuando aplique), persistiendo siempre `datetime_local`, `timezone` y `datetime_utc`.
- **Consecuencias:** Sincronización horaria exacta con las pasadas de ERA5-Land y GFS.

---

### DEC-007: Tratamiento de Anomalías de Coordenadas del CSV
- **Fecha:** 2026-08-29
- **Estado:** Aprobada / En vigor
- **Contexto:** 8 registros presentan coordenadas nulas y 2 registros presentan errores de tipeo en origen (Parral $-336.25^\circ$, Ercilla $-0.065^\circ$).
- **Decisión:** No modificar el CSV original. En la etapa de ingestión QA (`data/derived/`), generar flags de trazabilidad (`QA_NO_COORD`, `QA_COORD_CORRECTED`) y asignar coordenadas corregidas documentadas.
- **Consecuencias:** 68.538 de los 68.546 incendios (99,99 %) quedan plenamente geolocalizados en celdas H3.

---

### DEC-008: Congelamiento del Baseline M0 (BR-CONAF)
- **Fecha:** 2026-08-29
- **Estado:** Aprobada / En vigor
- **Contexto:** Necesidad de contar con una referencia inmutable de la regla original para evaluar mejoras cuantitativas.
- **Decisión:** Congelar M0 implementando:
  1. HCFM U. de Chile: $0.297374 + 0.262\cdot\mathrm{HR} - 0.00982\cdot T$.
  2. Hillshade SRTM 90 m (azimut 313°, altura 60°).
  3. Matriz PI 288 celdas de Rothermel/BehavePlus.
  4. Umbrales $\mathrm{PI} \ge 70\%$ y Viento $\ge 20\ \mathrm{km/h}$.
  5. Corrección de defectos técnicos no metodológicos (resampling bilineal restringido a bandas continuas, límites de dominio protegidos contra NoData).
- **Consecuencias:** Base de comparación fija para M1 (BR-CAL) y M2 (P-IGN).
