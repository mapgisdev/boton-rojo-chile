# Guía de Frontend GeoLibre y Publicación en Cloudflare R2 (Fase 10)

**Módulo:** `frontend/` y `src.shared.export_r2_pmtiles`  
**Tecnologías:** MapLibre GL JS, HTML5, CSS3 Glassmorphism, Cloudflare R2, Cloudflare Pages.

---

## 1. Arquitectura del Frontend GeoLibre

El Frontend de **BR-HR** es una interfaz web moderna, responsiva y de alto rendimiento diseñada para autoridades de emergencia (SENAPRED / CONAF) y la ciudadanía:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FRONTEND GEOLIBRE                                │
│                                                                             │
│  ┌─────────────────────────┐  ┌──────────────────────────────────────────┐  │
│  │   Panel Lateral (DOM)   │  │       Visor Cartográfico MapLibre        │  │
│  │ - Selector de Fechas    │  │ - 33.237 Hexágonos H3 (Res 8) Coloreados │  │
│  │ - Switch de Capas       │  │ - 346 Límites Comunales de Chile         │  │
│  │ - Leyendas Dinámicas    │  │ - Focos de Incendio (Megaincendios)      │  │
│  │ - Ranking Comunal       │  │ - Inspector Flotante al Clic             │  │
│  └─────────────────────────┘  └──────────────────────────────────────────┘  │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
            ┌──────────────────────────┴──────────────────────────┐
            ▼                                                     ▼
┌──────────────────────────────┐              ┌──────────────────────────────┐
│     FastAPI Backend API      │              │     Cloudflare R2 (CDN)      │
│  (Pronóstico en tiempo real) │              │  (Malla H3 y Archivos JSON)  │
└──────────────────────────────┘              └──────────────────────────────┘
```

---

## 2. Cómo Probar el Frontend Localmente

Puedes iniciar un servidor web local en el puerto 3000:

```bash
python -m http.server 3000 --directory frontend
```

Luego abre tu navegador en:
👉 **[http://localhost:3000](http://localhost:3000)**

---

## 3. Despliegue en Cloudflare Pages (Paso a Paso)

1. **Conectar Repositorio:**
   * En el panel de [Cloudflare Dashboard](https://dash.cloudflare.com/), ve a **Workers & Pages** > **Create application** > **Pages** > **Connect to Git**.
   * Selecciona el repositorio `BOTON_Rojo_Chile`.

2. **Configuración de Build:**
   * **Framework preset:** `None`
   * **Build output directory:** `frontend`
   * **Root directory:** `/` (o `/frontend`)

3. **Publicar:**
   * Haz clic en **Save and Deploy**. En menos de 30 segundos tu sitio web estará disponible globalmente en una URL segura tipo `https://boton-rojo-chile.pages.dev`.

---

## 4. Publicación de Datos en Cloudflare R2

Para exportar y sincronizar los artefactos estáticos (malla H3, límites comunales, pronósticos JSON) con tu bucket de Cloudflare R2:

```bash
# Exportar archivos localmente a data/r2_export/
python -m src.shared.export_r2_pmtiles
```
