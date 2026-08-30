/**
 * app.js — Controlador Frontend de Botón Rojo de Alta Resolución (BR-HR 2026) con MapLibre GL JS.
 * Soporta Zoom y Filtrado Automático por Comuna con Botón de Restauración ("Limpiar").
 */

// Configuración dinámica de Endpoints
const API_BASE = window.location.origin;

let map;
let communesGeoJSON = null;
let communesList = [];
let allFiresGeoJSON = null;
let communeH3Lookup = {};
let selectedCommuneFilter = null;
let activeEventDate = "LATEST";

// Coordenadas focales y configuración de los escenarios
const EVENT_CENTERS = {
  "2023-02-03": { center: [-72.5, -37.0], zoom: 7.0, name: "Megaincendios Biobío / Ñuble / Araucanía" },
  "2024-02-02": { center: [-71.4, -33.1], zoom: 8.5, name: "Megaincendio Viña del Mar / Quilpué (Valparaíso)" },
  "2017-01-20": { center: [-72.2, -35.6], zoom: 7.5, name: "Tormenta de Fuego Las Máquinas (Maule - 211.000 ha)" },
  "2023-01-15": { center: [-71.8, -35.8], zoom: 6.8, name: "Día Típico de Verano (Actividad Moderada)" },
  "2020-02-09": { center: [-72.6, -38.5], zoom: 7.5, name: "Ola de Calor Focalizada La Araucanía" },
  "2023-11-15": { center: [-71.0, -33.6], zoom: 7.4, name: "Primavera Central (Riesgo Temprano)" },
  "2023-07-15": { center: [-71.8, -36.0], zoom: 6.5, name: "Invierno Austral (Condición Normal)" },
  "LATEST":     { center: [-71.8, -36.0], zoom: 6.5, name: "Pronóstico Tiempo Real" }
};

// Paleta de colores oficial de BR-HR
const COLORS = {
  ROJO: "#d90429",
  ROJO_FILL: "rgba(217, 4, 41, 0.50)",
  AMARILLO: "#ffd166",
  AMARILLO_FILL: "rgba(255, 209, 102, 0.55)",
  TEMPRANA_FILL: "rgba(252, 191, 73, 0.30)",
  BORDER_RED: "#9b2226",
  BORDER_YELLOW: "#b45309",
  BORDER_NORMAL: "#64748b",
  TRANSPARENT: "rgba(0,0,0,0)"
};

// 1. Inicializar Mapa MapLibre GL
document.addEventListener("DOMContentLoaded", () => {
  initMap();
  setupEventListeners();
});

function initMap() {
  map = new maplibregl.Map({
    container: "map",
    style: {
      version: 8,
      sources: {
        "esri-gray": {
          type: "raster",
          tiles: [
            "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
          ],
          tileSize: 256,
          attribution: "Esri, HERE, Garmin, © OpenStreetMap"
        },
        "esri-labels": {
          type: "raster",
          tiles: [
            "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Reference/MapServer/tile/{z}/{y}/{x}"
          ],
          tileSize: 256
        }
      },
      layers: [
        { id: "base-gray", type: "raster", source: "esri-gray", minzoom: 0, maxzoom: 19 },
        { id: "base-labels", type: "raster", source: "esri-labels", minzoom: 0, maxzoom: 19 }
      ]
    },
    center: [-71.8, -36.0],
    zoom: 6.5,
    pitch: 0,
    bearing: 0
  });

  map.addControl(new maplibregl.NavigationControl(), "top-right");
  map.addControl(new maplibregl.ScaleControl({ maxWidth: 100, unit: "metric" }), "bottom-right");

  map.on("load", async () => {
    console.log("MapLibre inicializado. Cargando datos y capas...");
    await loadInitialData();
  });
}

// 2. Cargar Datos Base y Primer Evento
async function loadInitialData() {
  updateStatus("Cargando límites comunales e índices H3...");

  try {
    // A. Cargar Límites Comunales Base
    communesGeoJSON = await safeFetchJSON([
      "./data/r2_export/comunas_chile.geojson",
      "/data/r2_export/comunas_chile.geojson",
      "data/r2_export/comunas_chile.geojson"
    ]);

    // B. Cargar Diccionario de Celdas H3 por Comuna
    communeH3Lookup = await safeFetchJSON([
      "./data/r2_export/commune_h3_lookup.json",
      "/data/r2_export/commune_h3_lookup.json",
      "data/r2_export/commune_h3_lookup.json"
    ]) || {};

    // C. Cargar Universo Histórico CONAF (68.187 eventos)
    allFiresGeoJSON = await safeFetchJSON([
      "./data/r2_export/incendios_historicos_all.json",
      "/data/r2_export/incendios_historicos_all.json",
      "./data/r2_export/incendios_historicos_top.json",
      "/data/r2_export/incendios_historicos_top.json"
    ]);

    // D. Inicializar Fuentes en MapLibre
    if (communesGeoJSON) {
      map.addSource("comunas-mesh", { type: "geojson", data: communesGeoJSON });
    }

    map.addSource("h3-res7-mesh", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] }
    });

    map.addSource("h3-res8-centroids", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] }
    });

    map.addSource("fires-points", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] }
    });

    // =========================================================================
    // CONFIGURACIÓN DE CAPAS (ORDEN DE APILAMIENTO Z-INDEX: DE ABAJO HACIA ARRIBA)
    // =========================================================================

    // 1. CAPA INFERIOR: MAPA DE CALOR DE ALERTA BOTÓN ROJO (KDE del Modelo)
    map.addLayer({
      id: "alert-heatmap",
      type: "heatmap",
      source: "h3-res8-centroids",
      layout: { "visibility": "none" },
      paint: {
        "heatmap-weight": ["interpolate", ["linear"], ["get", "weight"], 0.35, 0.3, 1.0, 1.0, 2.0, 2.0],
        "heatmap-intensity": [
          "interpolate", ["linear"], ["zoom"],
          5, 0.35,
          7, 0.70,
          9, 1.20,
          12, 1.80
        ],
        "heatmap-color": [
          "interpolate",
          ["linear"],
          ["heatmap-density"],
          0, "rgba(0, 0, 0, 0)",
          0.20, "rgba(255, 209, 102, 0.45)",
          0.45, "#f77f00",
          0.70, "#d90429",
          1.0, "#6a040f"
        ],
        "heatmap-radius": [
          "interpolate", ["linear"], ["zoom"],
          5, 6,
          7, 12,
          9, 22,
          12, 38
        ],
        "heatmap-opacity": 0.82
      }
    });

    // 2. CAPA INTERMEDIA: HEXÁGONOS H3 RES 7 (SOBRE EL MAPA DE CALOR DE ALERTA)
    map.addLayer({
      id: "h3-res7-fill-yellow",
      type: "fill",
      source: "h3-res7-mesh",
      layout: { "visibility": "none" },
      filter: ["==", ["get", "alerta"], "AMARILLO"],
      paint: { "fill-color": COLORS.AMARILLO, "fill-opacity": 0.65 }
    });

    map.addLayer({
      id: "h3-res7-lines-yellow",
      type: "line",
      source: "h3-res7-mesh",
      layout: { "visibility": "none" },
      filter: ["==", ["get", "alerta"], "AMARILLO"],
      paint: { "line-color": "#b45309", "line-width": 1.1 }
    });

    map.addLayer({
      id: "h3-res7-fill-red",
      type: "fill",
      source: "h3-res7-mesh",
      layout: { "visibility": "none" },
      filter: ["==", ["get", "alerta"], "ROJO"],
      paint: { "fill-color": COLORS.ROJO, "fill-opacity": 0.70 }
    });

    map.addLayer({
      id: "h3-res7-lines-red",
      type: "line",
      source: "h3-res7-mesh",
      layout: { "visibility": "none" },
      filter: ["==", ["get", "alerta"], "ROJO"],
      paint: { "line-color": "#9b2226", "line-width": 1.2 }
    });

    // 3. CAPA INTERMEDIA SUPERIOR: COMUNAS CON ALERTA (SOBRE LOS HEXÁGONOS)
    if (communesGeoJSON) {
      map.addLayer({
        id: "comunas-fill",
        type: "fill",
        source: "comunas-mesh",
        layout: { "visibility": "visible" },
        paint: {
          "fill-color": [
            "case",
            [">=", ["get", "pct_rojo"], 30], "rgba(217, 4, 41, 0.35)",
            [">=", ["get", "pct_rojo"], 10], "rgba(255, 209, 102, 0.35)",
            [">", ["get", "pct_rojo"], 0], "rgba(252, 191, 73, 0.20)",
            COLORS.TRANSPARENT
          ],
          "fill-opacity": 0.75
        }
      });

      map.addLayer({
        id: "comunas-lines",
        type: "line",
        source: "comunas-mesh",
        layout: { "visibility": "visible" },
        paint: {
          "line-color": [
            "case",
            [">=", ["get", "pct_rojo"], 30], COLORS.BORDER_RED,
            [">=", ["get", "pct_rojo"], 10], COLORS.BORDER_YELLOW,
            COLORS.BORDER_NORMAL
          ],
          "line-width": [
            "case",
            [">=", ["get", "pct_rojo"], 10], 2.2,
            1.0
          ],
          "line-opacity": 0.95
        }
      });
    }

    // 4. CAPA SUPERIOR (TOP): MAPA DE CALOR DE INCENDIOS PONDERADO POR MAGNITUD (HA)
    map.addLayer({
      id: "fires-heatmap",
      type: "heatmap",
      source: "fires-points",
      layout: { "visibility": "none" },
      paint: {
        "heatmap-weight": [
          "interpolate",
          ["exponential", 1.5],
          ["get", "area_ha"],
          0.1, 0.05,
          5.0, 0.18,
          50.0, 0.60,
          200.0, 1.80,
          1000.0, 4.50,
          50000.0, 10.0
        ],
        "heatmap-intensity": [
          "interpolate", ["linear"], ["zoom"],
          5, 0.50,
          7, 0.95,
          10, 1.85,
          13, 2.50
        ],
        "heatmap-color": [
          "interpolate",
          ["linear"],
          ["heatmap-density"],
          0.00, "rgba(0, 0, 0, 0)",
          0.12, "rgba(10, 147, 150, 0.50)",
          0.30, "#ee9b00",
          0.55, "#ca6702",
          0.75, "#d90429",
          1.00, "#7209b7"
        ],
        "heatmap-radius": [
          "interpolate", ["linear"], ["zoom"],
          5, 8,
          7, 16,
          9, 26,
          12, 42
        ],
        "heatmap-opacity": 0.88
      }
    });

    // 5A. TODOS LOS FOCOS DE INCENDIO OBSERVADOS (CONAF) - Variación Sutil y Compacta
    map.addLayer({
      id: "fires-all-circles",
      type: "circle",
      source: "fires-points",
      layout: { "visibility": "none" },
      paint: {
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["get", "area_ha"],
          0.1, 2.8,
          5.0, 3.5,
          50.0, 4.4,
          200.0, 5.4,
          1000.0, 6.8,
          100000.0, 8.0
        ],
        "circle-color": [
          "case",
          [">=", ["get", "area_ha"], 1000], "#7209b7",
          [">=", ["get", "area_ha"], 200], "#d90429",
          [">=", ["get", "area_ha"], 50], "#f77f00",
          "#fcbf49"
        ],
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 1.0,
        "circle-opacity": 0.90
      }
    });

    // 5B. GRANDES Y MEGAINCENDIOS OBSERVADOS (≥ 200 ha) - Círculos Sutilmente Destacados
    map.addLayer({
      id: "fires-circles",
      type: "circle",
      source: "fires-points",
      layout: { "visibility": "none" },
      filter: [">=", ["get", "area_ha"], 200],
      paint: {
        "circle-radius": [
          "interpolate",
          ["linear"],
          ["get", "area_ha"],
          200, 5.2,
          1000, 6.6,
          10000, 8.0,
          100000, 9.5
        ],
        "circle-color": [
          "case",
          [">=", ["get", "area_ha"], 1000], "#7209b7",
          "#d90429"
        ],
        "circle-stroke-color": "#ffffff",
        "circle-stroke-width": 1.4,
        "circle-opacity": 0.92
      }
    });

    // 6. CAPA SATELITAL EN VIVO: FOCOS ACTIVOS NASA FIRMS (VIIRS 375m) - Puntos Satelitales Finos
    map.addSource("firms-points", {
      type: "geojson",
      data: { type: "FeatureCollection", features: [] }
    });

    map.addLayer({
      id: "firms-heatmap",
      type: "heatmap",
      source: "firms-points",
      layout: { "visibility": "none" },
      paint: {
        "heatmap-weight": ["interpolate", ["linear"], ["get", "frp_mw"], 1.0, 0.2, 50.0, 1.0, 500.0, 2.5],
        "heatmap-intensity": [
          "interpolate", ["linear"], ["zoom"],
          5, 0.45,
          7, 0.90,
          10, 1.60,
          13, 2.20
        ],
        "heatmap-color": [
          "interpolate",
          ["linear"],
          ["heatmap-density"],
          0.00, "rgba(0, 0, 0, 0)",
          0.15, "rgba(255, 183, 3, 0.50)",
          0.40, "#fb8500",
          0.70, "#d90429",
          1.00, "#ff0055"
        ],
        "heatmap-radius": [
          "interpolate", ["linear"], ["zoom"],
          5, 6,
          7, 12,
          9, 20,
          12, 35
        ],
        "heatmap-opacity": 0.82
      }
    });

    map.addLayer({
      id: "firms-points-layer",
      type: "circle",
      source: "firms-points",
      layout: { "visibility": "none" },
      paint: {
        "circle-radius": [
          "interpolate", ["linear"], ["zoom"],
          5, 1.8,
          8, 2.6,
          12, 4.2
        ],
        "circle-color": "#ff0055",
        "circle-stroke-color": "#ffe600",
        "circle-stroke-width": 0.6,
        "circle-opacity": 0.80
      }
    });

    setupMapInteractions();

    // Cargar Evento Inicial: Pronóstico Hoy (Tiempo Real)
    await loadForecastData("LATEST");

  } catch (error) {
    console.error("Error inicializando mapa:", error);
    updateStatus("Error al cargar capas.");
  }
}

// Helper de Fetch Resiliente con Múltiples Fallbacks (Compatible con Localhost, Cloudflare y GitHub Pages)
async function safeFetchJSON(urls) {
  const candidateUrls = [];
  for (const u of urls) {
    if (!u) continue;
    candidateUrls.push(u);
    if (u.startsWith("/")) {
      candidateUrls.push("." + u);
      candidateUrls.push(u.substring(1));
      candidateUrls.push("../" + u.substring(1));
    }
  }

  for (const url of candidateUrls) {
    try {
      const resp = await fetch(url);
      if (resp.ok) {
        return await resp.json();
      }
    } catch (e) {
      // Intentar siguiente URL
    }
  }
  return null;
}

// Helper: Verificar si un mes corresponde a la temporada de incendios de Chile (Diciembre a Marzo)
function isSummerFireSeason(dateStr) {
  if (!dateStr || dateStr.length < 7) return false;
  const month = parseInt(dateStr.substring(5, 7), 10);
  return month === 12 || month === 1 || month === 2 || month === 3;
}

// 3. Consultar y Actualizar TODAS las Capas del Evento Dinámicamente
async function loadForecastData(dateStr) {
  activeEventDate = dateStr;
  updateStatus(`Consultando datos para fecha: ${dateStr}...`);

  // Si había una comuna filtrada previamente, resetear el filtro
  if (selectedCommuneFilter) {
    resetCommuneFilter(false);
  }

  try {
    const isSpecialEvent = Object.keys(EVENT_CENTERS).includes(dateStr) && dateStr !== "LATEST";
    const basePath = isSpecialEvent ? `/data/r2_export/events/${dateStr}` : "/data/r2_export";

    let summary = null;
    let rawCommunes = null;
    let h3GeoJSON = null;
    let centroidsGeoJSON = null;
    let firesData = [];

    // E. Cargar Incendios Observados Específicos para la Fecha Seleccionada
    if (isSpecialEvent) {
      firesData = await safeFetchJSON([`${basePath}/fires.json`]) || [];
    } else if (allFiresGeoJSON && allFiresGeoJSON.features) {
      // Filtrar del universo histórico para la fecha exacta si coincide
      firesData = allFiresGeoJSON.features
        .filter(f => f.properties && f.properties.date === dateStr)
        .map(f => f.properties ? { ...f.properties, lon: f.geometry.coordinates[0], lat: f.geometry.coordinates[1] } : null)
        .filter(Boolean);
    }

    if (isSpecialEvent) {
      summary = await safeFetchJSON([`${basePath}/summary.json`]);
      rawCommunes = await safeFetchJSON([`${basePath}/communes.json`]);
      h3GeoJSON = await safeFetchJSON([`${basePath}/h3_res7.geojson`]);
      centroidsGeoJSON = await safeFetchJSON([`${basePath}/h3_centroids.json`]);
    } else if (firesData.length > 0 && isSummerFireSeason(dateStr)) {
      // SINTETIZADOR DINÁMICO: Si es temporada de incendios y hay focos activos, calcular alertas para esa fecha
      const dynamicResult = synthesizeDateForecast(dateStr, firesData);
      summary = dynamicResult.summary;
      rawCommunes = dynamicResult.communes;
      h3GeoJSON = dynamicResult.h3Mesh;
      centroidsGeoJSON = dynamicResult.centroids;
    } else {
      // Caso base / invierno / pronóstico normal
      summary = await safeFetchJSON([
        "/data/r2_export/summary.json",
        "/data/r2_export/br_hr_summary_latest.json",
        `${API_BASE}/api/v1/forecast/latest/summary`
      ]) || { red_alert_percentage: 0, total_cells: 33237, red_communes_count: 0, yellow_communes_count: 0 };

      rawCommunes = await safeFetchJSON([
        "/data/r2_export/communes.json",
        "/data/r2_export/br_hr_communes_latest.json",
        `${API_BASE}/api/v1/forecast/latest/communes`
      ]);
      h3GeoJSON = await safeFetchJSON([
        "/data/r2_export/h3_res7.geojson",
        "/data/r2_export/h3_chile_r7_mesh.geojson"
      ]);
      centroidsGeoJSON = await safeFetchJSON([
        "/data/r2_export/h3_centroids.json",
        "/data/r2_export/h3_chile_r8_centroids.json"
      ]);
    }

    communesList = rawCommunes || [];

    // Actualizar Malla H3
    if (h3GeoJSON && map.getSource("h3-res7-mesh")) {
      map.getSource("h3-res7-mesh").setData(h3GeoJSON);
    }

    // Actualizar Centroides de Calor de Alerta
    if (centroidsGeoJSON && map.getSource("h3-res8-centroids")) {
      map.getSource("h3-res8-centroids").setData(centroidsGeoJSON);
    }

    // Actualizar Focos de Incendios CONAF
    if (map.getSource("fires-points")) {
      const firesGeoJSON = {
        type: "FeatureCollection",
        features: firesData.map(f => ({
          type: "Feature",
          geometry: { type: "Point", coordinates: [f.lon, f.lat] },
          properties: f
        }))
      };
      map.getSource("fires-points").setData(firesGeoJSON);
    }

    // Actualizar Puntos Satelitales NASA FIRMS
    const firmsGeoJSON = await safeFetchJSON([
      `${basePath}/firms.json`,
      `${API_BASE}/api/v1/firms/active-points?days=1`,
      "/data/r2_export/firms_latest.json"
    ]);
    if (firmsGeoJSON && map.getSource("firms-points")) {
      map.getSource("firms-points").setData(firmsGeoJSON);
    }

    // F. Actualizar Comunas con las Alertas del Evento
    vincularAlertasAComunas();

    // G. Actualizar KPIs y Tabla
    updateKPIs(summary, communesList);
    renderCommunesTable(communesList);

    // H. Animación de Cámara al Epicentro del Evento si aplica
    if (EVENT_CENTERS[dateStr]) {
      const ev = EVENT_CENTERS[dateStr];
      map.flyTo({
        center: ev.center,
        zoom: ev.zoom,
        speed: 1.2,
        curve: 1.4,
        essential: true
      });
    } else if (firesData.length > 0) {
      // Centrar en el primer foco principal
      map.flyTo({
        center: [firesData[0].lon, firesData[0].lat],
        zoom: 7.6,
        speed: 1.2,
        duration: 1200
      });
    }

    const conafCount = firesData.length;
    const firmsCount = firmsGeoJSON ? (firmsGeoJSON.total_active_hotspots || (firmsGeoJSON.features ? firmsGeoJSON.features.length : 0)) : 0;
    const dateLabel = dateStr === 'LATEST' ? 'Pronóstico Hoy' : dateStr;
    updateStatus(`📅 ${dateLabel}  |  🔥 CONAF: ${conafCount.toLocaleString()} focos  |  🛰️ FIRMS: ${firmsCount.toLocaleString()} satelitales`);

  } catch (e) {
    console.error("Error al actualizar fecha:", e);
    updateStatus(`Fecha cargada: ${dateStr}`);
  }
}

// 3.1. Función de Síntesis Dinámica para Cualquier Fecha de Temporada de Incendios
function synthesizeDateForecast(dateStr, firesData) {
  const comFires = {};
  const regFires = new Set();

  firesData.forEach(f => {
    const cName = (f.comuna || "").toLowerCase().trim();
    if (cName) comFires[cName] = (comFires[cName] || 0) + 1;
    if (f.region) regFires.add(f.region.toLowerCase().trim());
  });

  // Sintetizar comunas
  const communes = [];
  let redComCount = 0;
  let yellowComCount = 0;

  if (communesGeoJSON && communesGeoJSON.features) {
    communesGeoJSON.features.forEach(feat => {
      const cName = (feat.properties.comuna || feat.properties.Comuna || "").trim();
      const cleanName = cName.toLowerCase();
      const region = feat.properties.region || feat.properties.Region || "Chile";
      const cleanReg = region.toLowerCase();

      const numFires = comFires[cleanName] || 0;
      let pctRojo = 0.0;
      let alerta = "NORMAL";

      if (numFires >= 2) {
        pctRojo = Math.min(95.0, 35.0 + numFires * 12.0);
        alerta = "ALERTA ROJA COMUNAL";
        redComCount++;
      } else if (numFires === 1) {
        pctRojo = 22.0;
        alerta = "ALERTA AMARILLA COMUNAL";
        yellowComCount++;
      } else if (regFires.has(cleanReg)) {
        pctRojo = 12.0;
        alerta = "ALERTA AMARILLA COMUNAL";
        yellowComCount++;
      }

      communes.push({
        codcom: String(feat.properties.cod_comuna || feat.properties.codcom || ""),
        comuna: cName,
        region: region,
        total_hexagons: 45,
        red_hexagons: Math.round((pctRojo / 100.0) * 45),
        yellow_hexagons: alerta.includes("AMARILLA") ? 8 : 0,
        pct_superficie_roja: pctRojo,
        alerta_comunal: alerta
      });
    });
  }

  // Sintetizar Centroides de Calor de Alerta basados en los focos
  const centroids = {
    type: "FeatureCollection",
    features: firesData.map((f, i) => ({
      type: "Feature",
      geometry: { type: "Point", coordinates: [f.lon, f.lat] },
      properties: {
        h3_id: `dyn_${i}`,
        weight: f.area_ha >= 100 ? 1.8 : 1.0,
        horas_br: f.area_ha >= 100 ? 4 : 2,
        p_ign: 0.82,
        alerta: f.area_ha >= 100 ? "ROJO" : "AMARILLO"
      }
    }))
  };

  const summary = {
    date: dateStr,
    total_cells: 33237,
    red_cells_count: redComCount * 14,
    yellow_cells_count: yellowComCount * 8,
    red_alert_percentage: Number(((redComCount / Math.max(1, communes.length)) * 100).toFixed(1)),
    total_communes: communes.length,
    red_communes_count: redComCount,
    yellow_communes_count: yellowComCount
  };

  return {
    summary,
    communes,
    h3Mesh: { type: "FeatureCollection", features: [] },
    centroids
  };
}

// 4. Vincular Alertas a Comunas
function vincularAlertasAComunas() {
  if (!communesGeoJSON || !communesList || communesList.length === 0) return;

  const comMap = {};
  communesList.forEach(c => {
    if (c.comuna) comMap[c.comuna.toLowerCase().trim()] = c;
    if (c.codcom) comMap[String(c.codcom).trim()] = c;
  });

  communesGeoJSON.features.forEach(feat => {
    const name = (feat.properties.comuna || feat.properties.Comuna || "").toLowerCase().trim();
    const cod = String(feat.properties.cod_comuna || feat.properties.codcom || "").trim();
    const match = comMap[name] || comMap[cod];

    if (match) {
      feat.properties.pct_rojo = match.pct_superficie_roja || 0;
      feat.properties.alerta = match.alerta_comunal || "NORMAL";
      feat.properties.total_h3 = match.total_hexagons || match.total_cells || 0;
      feat.properties.red_h3 = match.red_hexagons || match.red_cells_count || 0;
      feat.properties.region_name = match.region || feat.properties.region || feat.properties.Region || "";
    } else {
      feat.properties.pct_rojo = 0;
      feat.properties.alerta = "NORMAL";
      feat.properties.total_h3 = 0;
      feat.properties.red_h3 = 0;
      feat.properties.region_name = feat.properties.region || feat.properties.Region || "";
    }
  });

  if (map && map.getSource("comunas-mesh")) {
    map.getSource("comunas-mesh").setData(communesGeoJSON);
  }
}

// 5. FILTRADO Y ZOOM POR COMUNA SELECCIONADA
function filterByCommune(comunaName, codcom) {
  if (!comunaName) return;
  selectedCommuneFilter = comunaName;

  const cleanName = comunaName.toLowerCase().trim();
  const cleanCod = String(codcom || "").trim();

  // A. Buscar Bounding Box de la comuna en communesGeoJSON
  let targetFeature = null;
  if (communesGeoJSON && communesGeoJSON.features) {
    targetFeature = communesGeoJSON.features.find(f => {
      const fName = (f.properties.comuna || f.properties.Comuna || "").toLowerCase().trim();
      const fCod = String(f.properties.cod_comuna || f.properties.codcom || "").trim();
      return fName === cleanName || (cleanCod && fCod === cleanCod);
    });
  }

  if (targetFeature) {
    const bbox = calculateBBox(targetFeature);
    map.fitBounds(bbox, {
      padding: 60,
      maxZoom: 11.5,
      duration: 1200,
      essential: true
    });
  }

  // B. Obtener lista de celdas H3 asociadas a la comuna
  const lookupEntry = communeH3Lookup[cleanName] || (cleanCod ? communeH3Lookup[cleanCod] : null);
  const h7Ids = lookupEntry ? lookupEntry.h7_ids : [];
  const h8Ids = lookupEntry ? lookupEntry.h8_ids : [];

  // C. Aplicar Filtros en Capas de MapLibre

  // 1. Filtrar Comuna
  if (map.getLayer("comunas-fill")) {
    map.setFilter("comunas-fill", ["==", ["downcase", ["get", "comuna"]], cleanName]);
  }
  if (map.getLayer("comunas-lines")) {
    map.setFilter("comunas-lines", ["==", ["downcase", ["get", "comuna"]], cleanName]);
  }

  // 2. Filtrar Hexágonos H3 Res 7
  if (h7Ids.length > 0) {
    if (map.getLayer("h3-res7-fill-red")) {
      map.setFilter("h3-res7-fill-red", ["all", ["==", ["get", "alerta"], "ROJO"], ["in", ["get", "h3_id"], ["literal", h7Ids]]]);
    }
    if (map.getLayer("h3-res7-lines-red")) {
      map.setFilter("h3-res7-lines-red", ["all", ["==", ["get", "alerta"], "ROJO"], ["in", ["get", "h3_id"], ["literal", h7Ids]]]);
    }
    if (map.getLayer("h3-res7-fill-yellow")) {
      map.setFilter("h3-res7-fill-yellow", ["all", ["==", ["get", "alerta"], "AMARILLO"], ["in", ["get", "h3_id"], ["literal", h7Ids]]]);
    }
    if (map.getLayer("h3-res7-lines-yellow")) {
      map.setFilter("h3-res7-lines-yellow", ["all", ["==", ["get", "alerta"], "AMARILLO"], ["in", ["get", "h3_id"], ["literal", h7Ids]]]);
    }
  }

  // 3. Filtrar Mapa de Calor de Alerta (Res 8)
  if (h8Ids.length > 0 && map.getLayer("alert-heatmap")) {
    map.setFilter("alert-heatmap", ["in", ["get", "h3_id"], ["literal", h8Ids]]);
  }

  // 4. Filtrar Incendios de la Comuna
  if (map.getLayer("fires-heatmap")) {
    map.setFilter("fires-heatmap", ["==", ["downcase", ["get", "comuna"]], cleanName]);
  }
  if (map.getLayer("fires-circles")) {
    map.setFilter("fires-circles", ["all", [">=", ["get", "area_ha"], 200], ["==", ["downcase", ["get", "comuna"]], cleanName]]);
  }

  // D. Mostrar Botón Limpiar en el Panel
  const btnReset = document.getElementById("btn-reset-view");
  if (btnReset) btnReset.classList.remove("hidden");

  updateStatus(`Comuna seleccionada: ${comunaName}`);
}

// 6. RESTAURAR VISTA Y ELIMINAR FILTROS ("LIMPIAR")
function resetCommuneFilter(animate = true) {
  selectedCommuneFilter = null;

  // Restaurar filtros predeterminados de todas las capas
  if (map.getLayer("comunas-fill")) map.setFilter("comunas-fill", null);
  if (map.getLayer("comunas-lines")) map.setFilter("comunas-lines", null);

  if (map.getLayer("h3-res7-fill-red")) map.setFilter("h3-res7-fill-red", ["==", ["get", "alerta"], "ROJO"]);
  if (map.getLayer("h3-res7-lines-red")) map.setFilter("h3-res7-lines-red", ["==", ["get", "alerta"], "ROJO"]);
  if (map.getLayer("h3-res7-fill-yellow")) map.setFilter("h3-res7-fill-yellow", ["==", ["get", "alerta"], "AMARILLO"]);
  if (map.getLayer("h3-res7-lines-yellow")) map.setFilter("h3-res7-lines-yellow", ["==", ["get", "alerta"], "AMARILLO"]);

  if (map.getLayer("alert-heatmap")) map.setFilter("alert-heatmap", null);
  if (map.getLayer("fires-heatmap")) map.setFilter("fires-heatmap", null);
  if (map.getLayer("fires-circles")) map.setFilter("fires-circles", [">=", ["get", "area_ha"], 200]);

  // Ocultar Botón Limpiar
  const btnReset = document.getElementById("btn-reset-view");
  if (btnReset) btnReset.classList.add("hidden");

  // Ocultar Inspector
  document.getElementById("inspector-card").classList.add("hidden");

  // Re-enfocar la cámara en la vista general
  if (animate) {
    if (EVENT_CENTERS[activeEventDate]) {
      const ev = EVENT_CENTERS[activeEventDate];
      map.flyTo({ center: ev.center, zoom: ev.zoom, speed: 1.2, duration: 1200 });
    } else {
      map.flyTo({ center: [-71.8, -36.0], zoom: 6.5, speed: 1.2, duration: 1200 });
    }
  }

  updateStatus(`Vista general restaurada (${activeEventDate})`);
}

// Helper: Calcular Bounding Box de una Geometría GeoJSON
function calculateBBox(feature) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;

  function traverse(coords) {
    if (typeof coords[0] === "number") {
      const [x, y] = coords;
      if (x < minX) minX = x;
      if (y < minY) minY = y;
      if (x > maxX) maxX = x;
      if (y > maxY) maxY = y;
    } else {
      coords.forEach(traverse);
    }
  }

  if (feature.geometry && feature.geometry.coordinates) {
    traverse(feature.geometry.coordinates);
  }

  return [[minX, minY], [maxX, maxY]];
}

function updateKPIs(summary, communes) {
  if (!communes || communes.length === 0) return;
  const redCount = communes.filter(c => c.alerta_comunal && c.alerta_comunal.includes("ROJA")).length;
  const yellowCount = communes.filter(c => c.alerta_comunal && c.alerta_comunal.includes("AMARILLA")).length;
  const totalAlerted = redCount + yellowCount;

  document.getElementById("kpi-red-communes").innerText = redCount;
  document.getElementById("kpi-yellow-communes").innerText = yellowCount;

  // Actualizar el número de comunas con algún nivel de alerta (Roja o Amarilla) en el label de la capa
  const layerLabel = document.getElementById("label-layer-comunas");
  if (layerLabel) {
    layerLabel.innerHTML = `<strong>🏛️ Comunas en Botón Rojo (${totalAlerted})</strong>`;
  }

  if (summary && summary.red_alert_percentage !== undefined) {
    document.getElementById("kpi-risk-pct").innerText = `${summary.red_alert_percentage} %`;
  } else if (summary && summary.pct_territorio_rojo !== undefined) {
    document.getElementById("kpi-risk-pct").innerText = `${summary.pct_territorio_rojo} %`;
  }
}

function renderCommunesTable(communes) {
  const tbody = document.getElementById("communes-tbody");
  tbody.innerHTML = "";

  const sorted = [...communes].sort((a, b) => (b.pct_superficie_roja || 0) - (a.pct_superficie_roja || 0));

  sorted.slice(0, 35).forEach(com => {
    const tr = document.createElement("tr");
    const isRed = (com.pct_superficie_roja || 0) >= 30;
    const isYellow = (com.pct_superficie_roja || 0) >= 10 && !isRed;
    const badgeClass = isRed ? "rojo" : (isYellow ? "amarillo" : "verde");
    const badgeText = isRed ? "ROJA" : (isYellow ? "AMARILLA" : "NORMAL");

    tr.innerHTML = `
      <td><strong>${com.comuna}</strong></td>
      <td><small>${com.region ? com.region.replace("Región de", "").replace("Región del", "").replace("Región de los", "").trim() : ""}</small></td>
      <td><strong>${(com.pct_superficie_roja || 0).toFixed(1)}%</strong></td>
      <td><span class="badge-alert ${badgeClass}">${badgeText}</span></td>
    `;

    // Clic en fila de comuna activa el ZOOM y FILTRADO territorial
    tr.addEventListener("click", () => {
      openCommuneDetail(com);
      filterByCommune(com.comuna, com.codcom);
    });

    tbody.appendChild(tr);
  });
}

// 7. Interacciones y Clics
function setupMapInteractions() {
  map.on("click", "comunas-fill", (e) => {
    if (!e.features || e.features.length === 0) return;
    const props = e.features[0].properties;
    const comName = props.comuna || props.Comuna;
    const codcom = props.cod_comuna || props.codcom;

    openCommuneDetail({
      comuna: comName,
      region: props.region_name || props.region || props.Region,
      pct_superficie_roja: props.pct_rojo,
      total_hexagons: props.total_h3,
      red_hexagons: props.red_h3,
      alerta_comunal: props.alerta
    });

    // Filtrar y hacer zoom a la comuna seleccionada
    filterByCommune(comName, codcom);
  });

  map.on("click", "h3-res7-fill-red", (e) => handleHexClick(e, "BOTÓN ROJO", "rojo"));
  map.on("click", "h3-res7-fill-yellow", (e) => handleHexClick(e, "ALERTA AMARILLA", "amarillo"));

  function handleHexClick(e, alertaLabel, badgeClass) {
    if (!e.features || e.features.length === 0) return;
    const props = e.features[0].properties;
    showInspector(`📍 Sector H3 (Res 7, ~500 ha)`, `
      <p><strong>ID Hexágono:</strong> <code>${props.h3_id}</code></p>
      <p><strong>Nivel de Alerta:</strong> <span class="badge-alert ${badgeClass}">${alertaLabel}</span></p>
      <p><strong>Horas Botón Rojo:</strong> ${props.horas_br || 0} hrs continuas</p>
      <p><strong>Probabilidad Ignición Promedio:</strong> ${((props.p_ign || 0) * 100).toFixed(1)}%</p>
      <p><strong>Superficie en Alerta Roja:</strong> ${(props.pct_rojo || 0).toFixed(1)}%</p>
    `);
  }

  map.on("click", "fires-all-circles", (e) => {
    if (!e.features || e.features.length === 0) return;
    const props = e.features[0].properties;
    const ha = parseFloat(props.area_ha || 1.0);
    const tipo = ha >= 1000 ? "🟣 MEGAINCENDIO" : (ha >= 200 ? "🔴 GRAN INCENDIO" : (ha >= 50 ? "🟠 MEDIANO" : "🟡 MENOR"));
    showInspector("🔥 Foco de Incendio Registrado (CONAF)", `
      <p><strong>Comuna:</strong> ${props.comuna || 'Sin especificar'} (${props.region || ''})</p>
      <p><strong>Fecha Registro:</strong> ${props.date || '--'}</p>
      <p><strong>Superficie Afectada:</strong> <strong>${ha.toLocaleString()} ha</strong></p>
      <p><strong>Clasificación:</strong> ${tipo}</p>
    `);
  });

  map.on("click", "fires-circles", (e) => {
    if (!e.features || e.features.length === 0) return;
    const props = e.features[0].properties;
    const tipo = props.area_ha >= 1000 ? "🟣 MEGAINCENDIO" : (props.area_ha >= 100 ? "🔴 GRAN INCENDIO" : "🟠 MEDIANO");
    showInspector("🔥 Gran Incendio Forestal (CONAF)", `
      <p><strong>Comuna:</strong> ${props.comuna} (${props.region})</p>
      <p><strong>Fecha Inicio:</strong> ${props.date}</p>
      <p><strong>Superficie Quemada:</strong> <strong>${props.area_ha} ha</strong></p>
      <p><strong>Categoría:</strong> ${tipo}</p>
    `);
  });

  map.on("click", "firms-points-layer", (e) => {
    if (!e.features || e.features.length === 0) return;
    const props = e.features[0].properties;
    showInspector("🛰️ Anomalía Térmica Satelital (NASA FIRMS)", `
      <p><strong>Sensor Satelital:</strong> ${props.sensor || 'VIIRS 375m NRT'}</p>
      <p><strong>Satélite:</strong> ${props.satellite || 'SNPP / NOAA-20'}</p>
      <p><strong>Temperatura de Brillo:</strong> <strong>${props.brightness_c || '--'} °C</strong> (${props.brightness_k || '--'} K)</p>
      <p><strong>Potencia Radiativa (FRP):</strong> ${props.frp_mw || '--'} MW</p>
      <p><strong>Nivel de Confianza:</strong> <span class="badge-alert rojo">${props.confidence || 'Nominal'}</span></p>
      <p><strong>Hora Local Chile:</strong> <strong>${props.time_local || props.date}</strong></p>
      <p><strong>Hora Satélite UTC:</strong> ${props.time_utc || '--'}</p>
    `);
  });

  map.on("mouseenter", "comunas-fill", () => map.getCanvas().style.cursor = "pointer");
  map.on("mouseleave", "comunas-fill", () => map.getCanvas().style.cursor = "");
  map.on("mouseenter", "h3-res7-fill-red", () => map.getCanvas().style.cursor = "pointer");
  map.on("mouseleave", "h3-res7-fill-red", () => map.getCanvas().style.cursor = "");
  map.on("mouseenter", "h3-res7-fill-yellow", () => map.getCanvas().style.cursor = "pointer");
  map.on("mouseleave", "h3-res7-fill-yellow", () => map.getCanvas().style.cursor = "");
  map.on("mouseenter", "fires-all-circles", () => map.getCanvas().style.cursor = "pointer");
  map.on("mouseleave", "fires-all-circles", () => map.getCanvas().style.cursor = "");
  map.on("mouseenter", "fires-circles", () => map.getCanvas().style.cursor = "pointer");
  map.on("mouseleave", "fires-circles", () => map.getCanvas().style.cursor = "");
  map.on("mouseenter", "firms-points-layer", () => map.getCanvas().style.cursor = "pointer");
  map.on("mouseleave", "firms-points-layer", () => map.getCanvas().style.cursor = "");
}

function showInspector(title, htmlContent) {
  const card = document.getElementById("inspector-card");
  document.getElementById("insp-title").innerText = title;
  document.getElementById("insp-content").innerHTML = htmlContent;
  card.classList.remove("hidden");
}

function openCommuneDetail(com) {
  const isRed = (com.pct_superficie_roja || 0) >= 30;
  const isYellow = (com.pct_superficie_roja || 0) >= 10 && !isRed;
  const badgeClass = isRed ? "rojo" : (isYellow ? "amarillo" : "verde");

  showInspector(`🏛️ Comuna: ${com.comuna}`, `
    <p><strong>Región:</strong> ${com.region}</p>
    <p><strong>Superficie en Botón Rojo:</strong> <strong>${(com.pct_superficie_roja || 0).toFixed(1)}%</strong></p>
    <p><strong>Total Hexágonos H3:</strong> ${com.total_hexagons || com.total_cells || 0}</p>
    <p><strong>Hexágonos en Alerta Roja:</strong> ${com.red_hexagons || com.red_cells_count || 0}</p>
    <p><strong>Alerta SENAPRED:</strong> <span class="badge-alert ${badgeClass}">${com.alerta_comunal || 'NORMAL'}</span></p>
  `);
}

// 8. Event Listeners
function setupEventListeners() {
  document.getElementById("event-select").addEventListener("change", (e) => {
    const val = e.target.value;
    loadForecastData(val);
  });

  document.getElementById("commune-search").addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase().trim();
    const filtered = communesList.filter(c => c.comuna.toLowerCase().includes(query) || (c.region && c.region.toLowerCase().includes(query)));
    renderCommunesTable(filtered);
  });

  // Botón Limpiar Filtro Comunal
  const btnReset = document.getElementById("btn-reset-view");
  if (btnReset) {
    btnReset.addEventListener("click", () => {
      resetCommuneFilter(true);
    });
  }

  // 1. Capa Comunas
  document.getElementById("layer-comunas").addEventListener("change", (e) => {
    const vis = e.target.checked ? "visible" : "none";
    if (map.getLayer("comunas-fill")) map.setLayoutProperty("comunas-fill", "visibility", vis);
    if (map.getLayer("comunas-lines")) map.setLayoutProperty("comunas-lines", "visibility", vis);
  });

  // 2. Hexágonos Res 7 Rojos
  document.getElementById("layer-h3-red").addEventListener("change", (e) => {
    const vis = e.target.checked ? "visible" : "none";
    if (map.getLayer("h3-res7-fill-red")) map.setLayoutProperty("h3-res7-fill-red", "visibility", vis);
    if (map.getLayer("h3-res7-lines-red")) map.setLayoutProperty("h3-res7-lines-red", "visibility", vis);
  });

  // 3. Hexágonos Res 7 Amarillos
  document.getElementById("layer-h3-yellow").addEventListener("change", (e) => {
    const vis = e.target.checked ? "visible" : "none";
    if (map.getLayer("h3-res7-fill-yellow")) map.setLayoutProperty("h3-res7-fill-yellow", "visibility", vis);
    if (map.getLayer("h3-res7-lines-yellow")) map.setLayoutProperty("h3-res7-lines-yellow", "visibility", vis);
  });

  // 4. Mapa de Calor de Alerta Botón Rojo
  toggleLayerCheckbox("layer-alert-kde", "alert-heatmap");

  // 5. Capa Satelital NASA FIRMS en Vivo
  const firmsChk = document.getElementById("layer-firms");
  if (firmsChk) {
    firmsChk.addEventListener("change", (e) => {
      if (map.getLayer("firms-points-layer")) {
        map.setLayoutProperty("firms-points-layer", "visibility", e.target.checked ? "visible" : "none");
      }
    });
  }

  // 6. Mapa de Calor Satelital NASA FIRMS
  toggleLayerCheckbox("layer-firms-kde", "firms-heatmap");

  // 7. Focos de Incendio y KDE de Incendios Observados
  toggleLayerCheckbox("layer-fires-all", "fires-all-circles");
  toggleLayerCheckbox("layer-fires", "fires-circles");
  toggleLayerCheckbox("layer-fires-kde", "fires-heatmap");

  // Cerrar Inspector
  document.getElementById("btn-close-inspector").addEventListener("click", () => {
    document.getElementById("inspector-card").classList.add("hidden");
  });
}

function toggleLayerCheckbox(checkboxId, layerId) {
  const chk = document.getElementById(checkboxId);
  if (!chk) return;
  chk.addEventListener("change", (e) => {
    if (map.getLayer(layerId)) {
      map.setLayoutProperty(layerId, "visibility", e.target.checked ? "visible" : "none");
    }
  });
}

function updateStatus(text) {
  const el = document.getElementById("status-date-info");
  if (el) el.innerText = text;
}
