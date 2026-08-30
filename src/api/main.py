"""
src/api/main.py — Punto de entrada principal de la API REST y Visor GeoLibre de BR-HR (FastAPI).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import router

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = ROOT / "frontend"
R2_EXPORT_DIR = ROOT / "data" / "r2_export"

app = FastAPI(
    title="BR-HR — Botón Rojo de Alta Resolución API",
    description="""
    API REST y Visor Web GeoLibre para pronósticos subcomunales (H3 resolución 8) y comunales
    del modelo Botón Rojo de Alta Resolución para Chile (BR-HR).
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuración de CORS para clientes web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

# Montar datos estáticos de R2 / GeoJSON si existen
if R2_EXPORT_DIR.exists():
    app.mount("/data/r2_export", StaticFiles(directory=str(R2_EXPORT_DIR)), name="r2_export")


# Rutas para servir el Frontend GeoLibre de forma transparente en /, /app, y /app/
@app.get("/styles.css", include_in_schema=False)
async def get_styles() -> FileResponse:
    return FileResponse(str(FRONTEND_DIR / "styles.css"), media_type="text/css")


@app.get("/app.js", include_in_schema=False)
async def get_app_js() -> FileResponse:
    return FileResponse(str(FRONTEND_DIR / "app.js"), media_type="application/javascript")


@app.get("/app", include_in_schema=False)
@app.get("/app/", include_in_schema=False)
@app.get("/", tags=["General"])
async def root() -> Any:
    """Sirve la aplicación web interactiva GeoLibre en /, /app o /app/."""
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file), media_type="text/html")

    return JSONResponse(
        content={
            "service": "BR-HR API — Botón Rojo de Alta Resolución",
            "version": "1.0.0",
            "documentation": "/docs",
            "health_check": "/health",
            "latest_summary": "/api/v1/forecast/latest/summary",
            "communes": "/api/v1/forecast/latest/communes",
            "status": "online",
        }
    )


# Montar estáticos adicionales si aplica
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    print(f"🔥 Iniciando servidor BR-HR en http://localhost:{port}")
    print(f"👉 Visor Web GeoLibre disponible en: http://localhost:{port}")
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port, reload=True)
