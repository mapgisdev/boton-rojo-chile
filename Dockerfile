# Dockerfile para despliegue de la API BR-HR en Railway / Google Cloud Run / Render
FROM python:3.11-slim

# Evitar prompts interactivos y buffering de logs
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

WORKDIR /app

# Instalar dependencias del sistema mínimas requeridas por GDAL/GEOS si aplica
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código fuente, frontend y datos requeridos
COPY src/ ./src/
COPY frontend/ ./frontend/
COPY data/ ./data/
COPY insumos/ ./insumos/

EXPOSE 8000

# Comando de inicio con soporte de puerto dinámico de Railway ($PORT)
CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
