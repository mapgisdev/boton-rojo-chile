# BR-HR — Paquete de arranque para Google Antigravity

Este workspace contiene el contexto, las reglas, la metodología y el blueprint técnico para guiar el desarrollo de **BR-HR (Botón Rojo de Alta Resolución)**.

## 1. Antes de abrir el proyecto en Antigravity

Copiar dentro de `insumos/` **sin modificar ni renombrar los originales**:

1. `Boton_Rojo.zip`
2. `Consolidado_incendios_2014_2024_temporada(1).csv`

El paquete NO incluye esos dos archivos porque deben conservarse como insumos fuente separados.

La estructura esperada será:

```text
BRHR_Antigravity_Package/
├── GEMINI.md
├── AGENTS.md
├── SUPERPROMPT_ANTIGRAVITY.md
├── .antigravity/
│   └── rules.md
├── docs/
├── prompts/
├── templates/
└── insumos/
    ├── Boton_Rojo.zip
    ├── Consolidado_incendios_2014_2024_temporada(1).csv
    └── LEEME_INSUMOS.md
```

## 2. Cómo iniciar

1. Abrir esta carpeta completa como workspace en Antigravity.
2. Confirmar que los dos archivos anteriores están en `insumos/`.
3. Pegar como primera instrucción el contenido de `SUPERPROMPT_ANTIGRAVITY.md`.
4. Pedir al agente que lea primero `GEMINI.md`, `.antigravity/rules.md` y todos los documentos de `docs/`.
5. **No empezar reescribiendo el sistema.** La primera salida obligatoria debe ser:
   - inventario de los insumos;
   - auditoría del sistema Botón Rojo legado;
   - perfil QA/QC del CSV 2014–2024;
   - mapa de dependencias;
   - `PLAN_IMPLEMENTACION.md`;
   - lista de supuestos, riesgos y pruebas de aceptación.
6. Revisar/aprobar el plan antes de pasar a una refactorización grande.

## 3. Principio central

El objetivo NO es fabricar una cuadrícula de apariencia más fina mediante interpolación.

El objetivo es construir un producto científicamente defendible que:

- preserve la réplica del Botón Rojo original;
- calibre la metodología con incendios reales;
- incorpore variables de mayor detalle;
- produzca resultados en raster ambiental de 250 m;
- entregue resultados operacionales en H3 resolución 8;
- agregue a comuna;
- entregue probabilidades calibradas e incertidumbre;
- pueda operar principalmente con Earth Engine + API ligera + R2 + GeoLibre.

## 4. Arquitectura tecnológica objetivo del MVP

```text
Fuentes
  ↓
Google Earth Engine
  ├── variables ambientales
  ├── baseline BR-CONAF
  ├── BR calibrado
  ├── P(ignición)
  ├── H3
  └── comuna
  ↓
Earth Engine REST
  ↓
Railway API ───────── R2
  ↓                    ↓
        GeoLibre
           ↓
Cloudflare Pages/Workers
```

**PostgreSQL/PostGIS no es obligatorio para el MVP.**

**Python se usa intensivamente para ciencia, QA/QC, entrenamiento y backtesting, pero no tiene que estar en cada solicitud operacional.**

## 5. Documentos más importantes

- `SUPERPROMPT_ANTIGRAVITY.md`: instrucción maestra.
- `docs/01_VISION_Y_ALCANCE.md`: objetivo y productos.
- `docs/02_METODOLOGIA_CIENTIFICA.md`: diseño científico.
- `docs/03_BLUEPRINT_TECNICO.md`: arquitectura tecnológica.
- `docs/04_DATASET_MAESTRO.md`: diseño H3×hora.
- `docs/05_PLAN_DE_DESARROLLO.md`: fases y criterios de salida.
- `docs/06_CONTRATO_API.md`: API propuesta.
- `docs/07_ARQUITECTURA_EARTH_ENGINE.md`: módulos GEE.
- `docs/08_VALIDACION_QAQC.md`: validación y backtesting.
- `docs/09_DECISIONES_NO_NEGOCIABLES.md`: límites que el agente no debe romper.
- `docs/10_REFERENCIAS_TECNICAS.md`: referencias y documentación.
