/**
 * app.js — Controlador Frontend de Botón Rojo de Alta Resolución (BR-HR 2026) con MapLibre GL JS.
 * Soporta Comparación Metodológica Dual (M0 Original CONAF vs BR-HR Calibrado 2026),
 * Zoom y Filtrado Automático por Comuna con Botón de Restauración ("Limpiar").
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
let currentModelMode = "BR_HR"; // "BR_HR" | "M0" | "BOTH"

// Registro Canónico de Comunas en Alerta Roja Oficial según Metodología M0 CONAF (Línea Base)
const M0_CANONICAL_RED_COMMUNES = {
  "2023-02-03": ["08301", "08303", "los angeles", "cabrero"],
  "2024-02-02": [],
  "2017-01-20": [
    "07102", "07103", "07201", "07306", "07304", "07305", "07204",
    "06206", "06306", "06204", "06205", "06201", "06202", "06203",
    "constitucion", "empedrado", "cauquenes", "san javier", "vichuquen",
    "hualane", "licanten", "paredones", "pumanque", "marchigue", "navidad",
    "pichilemu", "la estrella", "litueche"
  ],
  "2020-02-09": ["09106", "galvarino"],
  "2023-01-15": [],
  "2023-11-15": [],
  "2023-07-15": [],
  "LATEST": []
};

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

// Paleta de colores oficial de BR-HR y M0
const COLORS = {
  ROJO: "#d90429",
  ROJO_FILL: "rgba(217, 4, 41, 0.50)",
  M0_ROJO: "#800f2f",
  M0_FILL: "rgba(155, 34, 38, 0.65)",
  AMARILLO: "#ffd166",
  AMARILLO_FILL: "rgba(255, 209, 102, 0.55)",
  TEMPRANA_FILL: "rgba(252, 191, 73, 0.30)",
  BORDER_RED: "#9b2226",
  BORDER_M0: "#4a0419",
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

    // 1. MAPA DE CALOR DE ALERTA BOTÓN ROJO (KDE del Modelo)
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

    // 2. HEXÁGONOS H3 RES 7 (SOBRE EL MAPA DE CALOR)
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

    // 3A. COMUNAS CON ALERTA BR-HR CALIBRADAS (ROJA / AMARILLA)
    if (communesGeoJSON) {
      map.addLayer({
        id: "comunas-fill",
        type: "fill",
        source: "comunas-mesh",
        layout: { "visibility": "visible" },
        paint: {
          "fill-color": [
            "case",
            ["==", ["coalesce", ["get", "alerta"], ""], "ALERTA ROJA COMUNAL"], "rgba(217, 4, 41, 0.40)",
            ["==", ["coalesce", ["get", "alerta"], ""], "ALERTA AMARILLA COMUNAL"], "rgba(255, 209, 102, 0.45)",
            ["==", ["coalesce", ["get", "alerta"], ""], "ALERTA TEMPRANA PREVENTIVA"], "rgba(252, 191, 73, 0.30)",
            [">=", ["coalesce", ["get", "pct_rojo"], 0], 30], "rgba(217, 4, 41, 0.40)",
            [">=", ["coalesce", ["get", "pct_rojo"], 0], 10], "rgba(255, 209, 102, 0.45)",
            COLORS.TRANSPARENT
          ],
          "fill-opacity": 0.80
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
            ["==", ["coalesce", ["get", "alerta"], ""], "ALERTA ROJA COMUNAL"], COLORS.BORDER_RED,
            ["==", ["coalesce", ["get", "alerta"], ""], "ALERTA AMARILLA COMUNAL"], COLORS.BORDER_YELLOW,
            [">=", ["coalesce", ["get", "pct_rojo"], 0], 30], COLORS.BORDER_RED,
            [">=", ["coalesce", ["get", "pct_rojo"], 0], 10], COLORS.BORDER_YELLOW,
            COLORS.BORDER_NORMAL
          ],
          "line-width": [
            "case",
            ["==", ["coalesce", ["get", "alerta"], ""], "ALERTA ROJA COMUNAL"], 2.2,
            ["==", ["coalesce", ["get", "alerta"], ""], "ALERTA AMARILLA COMUNAL"], 2.0,
            [">=", ["coalesce", ["get", "pct_rojo"], 0], 10], 2.0,
            1.0
          ],
          "line-opacity": 0.85
        }
      });

      // 3B. CAPA BOTÓN ROJO ORIGINAL CONAF (M0 - LÍNEA BASE OFICIAL)
      map.addLayer({
        id: "comunas-m0-fill",
        type: "fill",
        source: "comunas-mesh",
        layout: { "visibility": "none" },
        paint: {
          "fill-color": [
            "case",
            ["==", ["coalesce", ["get", "is_m0_red"], false], true], "rgba(128, 15, 47, 0.65)",
            COLORS.TRANSPARENT
          ],
          "fill-opacity": 0.85
        }
      });

      map.addLayer({
        id: "comunas-m0-lines",
        type: "line",
        source: "comunas-mesh",
        layout: { "visibility": "none" },
        paint: {
          "line-color": [
            "case",
            ["==", ["coalesce", ["get", "is_m0_red"], false], true], COLORS.BORDER_M0,
            "rgba(100, 116, 139, 0.35)"
          ],
          "line-width": [
            "case",
            ["==", ["coalesce", ["get", "is_m0_red"], false], true], 2.8,
            0.6
          ],
          "line-opacity": 0.90
        }
      });
    }

    // 4. MAPA DE CALOR DE INCENDIOS PONDERADO POR MAGNITUD (HA)
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

    // 5A. TODOS LOS FOCOS DE INCENDIO OBSERVADOS (CONAF)
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

    // 5B. GRANDES Y MEGAINCENDIOS OBSERVADOS (≥ 200 ha)
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

    // 6. CAPA SATELITAL NASA FIRMS
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

// Helper de Fetch Resiliente
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
      // Intentar con la siguiente URL candidata
    }
  }
  return null;
}

// 3. Cargar Datos por Evento Seleccionado
async function loadForecastData(dateStr) {
  activeEventDate = dateStr;
  updateStatus(`Cargando datos para ${dateStr}...`);

  try {
    resetCommuneFilter(false);

    let summary = null;
    let rawCommunes = null;
    let h3GeoJSON = null;
    let centroidsGeoJSON = null;

    const isSpecialEvent = dateStr !== "LATEST";
    const basePath = isSpecialEvent ? `./data/r2_export/events/${dateStr}` : "./data/r2_export";

    // Extraer focos de incendios históricos de CONAF
    let firesData = [];
    if (isSpecialEvent && allFiresGeoJSON && Array.isArray(allFiresGeoJSON)) {
      firesData = allFiresGeoJSON.filter(f => f.date === dateStr);
    }

    if (isSpecialEvent) {
      summary = await safeFetchJSON([`${basePath}/summary.json`]);
      rawCommunes = await safeFetchJSON([`${basePath}/communes.json`]);
      h3GeoJSON = await safeFetchJSON([`${basePath}/h3_res7.geojson`]);
      centroidsGeoJSON = await safeFetchJSON([`${basePath}/h3_centroids.json`]);
    } else {
      summary = await safeFetchJSON([
        "./data/r2_export/summary.json",
        "/data/r2_export/summary.json",
        "data/r2_export/summary.json"
      ]) || { red_alert_percentage: 0, total_communes: 346, red_communes_count: 0, yellow_communes_count: 0 };

      rawCommunes = await safeFetchJSON([
        "./data/r2_export/communes.json",
        "/data/r2_export/communes.json",
        "data/r2_export/communes.json"
      ]);
      h3GeoJSON = await safeFetchJSON([
        "./data/r2_export/h3_res7.geojson",
        "/data/r2_export/h3_res7.geojson",
        "data/r2_export/h3_res7.geojson"
      ]);
      centroidsGeoJSON = await safeFetchJSON([
        "./data/r2_export/h3_centroids.json",
        "/data/r2_export/h3_centroids.json",
        "data/r2_export/h3_centroids.json"
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
      "./data/r2_export/firms_latest.json",
      "/data/r2_export/firms_latest.json",
      "data/r2_export/firms_latest.json"
    ]);
    if (firmsGeoJSON && map.getSource("firms-points")) {
      map.getSource("firms-points").setData(firmsGeoJSON);
    }

    // Vincular Alertas a Comunas (Calculando M0 y BR-HR)
    vincularAlertasAComunas(dateStr);

    // Actualizar KPIs y Tabla
    updateKPIs(summary, communesList, dateStr);
    renderCommunesTable(communesList);

    // Animación de Cámara al Epicentro del Evento si aplica
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

    // Sincronizar visibilidad según el modo de modelo actual
    aplicarModoModelo(currentModelMode);

  } catch (e) {
    console.error("Error al actualizar fecha:", e);
    updateStatus(`Fecha cargada: ${dateStr}`);
  }
}

// 4. Vincular Alertas a Comunas (Tanto para BR-HR como para M0 Oficial)
function vincularAlertasAComunas(dateStr) {
  if (!communesGeoJSON || !communesList || communesList.length === 0) return;

  const m0CanonicalList = M0_CANONICAL_RED_COMMUNES[dateStr] || [];

  const comMap = {};
  communesList.forEach(c => {
    if (c.comuna) {
      const cNorm = c.comuna.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim();
      comMap[cNorm] = c;
      comMap[c.comuna.toLowerCase().trim()] = c;
    }
    if (c.codcom) {
      const strCod = String(c.codcom).trim();
      comMap[strCod] = c;
      comMap[String(parseInt(strCod, 10))] = c;
    }
  });

  communesGeoJSON.features.forEach(feat => {
    const rawName = feat.properties.comuna || feat.properties.Comuna || feat.properties.NOM_COM || "";
    const name = rawName.toLowerCase().trim();
    const nameNorm = name.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    const cod = String(feat.properties.cod_comuna || feat.properties.codcom || feat.properties.CUT || "").trim();
    const codInt = String(parseInt(cod, 10));

    const match = comMap[cod] || comMap[codInt] || comMap[nameNorm] || comMap[name];

    // Verificar si la comuna estaba en Alerta Roja bajo la metodología M0 Original CONAF
    let isM0Red = false;
    if (m0CanonicalList.length > 0) {
      isM0Red = m0CanonicalList.includes(cod) || m0CanonicalList.includes(codInt) || m0CanonicalList.includes(name) || m0CanonicalList.includes(nameNorm);
    } else if (match && (match.is_m0_rojo === true || (match.pct_m0_rojo && match.pct_m0_rojo >= 30.0))) {
      isM0Red = true;
    }

    if (match) {
      feat.properties.pct_rojo = match.pct_superficie_roja || 0;
      feat.properties.pct_amarillo = match.pct_superficie_amarilla || 0;
      feat.properties.alerta = match.alerta_comunal || "NORMAL";
      feat.properties.total_h3 = match.total_hexagons || match.total_cells || 0;
      feat.properties.red_h3 = match.red_hexagons || match.red_cells_count || 0;
      feat.properties.region_name = match.region || feat.properties.region || feat.properties.Region || "";
      feat.properties.is_m0_red = isM0Red;
      feat.properties.m0_alerta = isM0Red ? "ROJO" : "NORMAL";
      match.is_m0_red = isM0Red;
    } else {
      feat.properties.pct_rojo = 0;
      feat.properties.pct_amarillo = 0;
      feat.properties.alerta = "NORMAL";
      feat.properties.total_h3 = 0;
      feat.properties.red_h3 = 0;
      feat.properties.region_name = feat.properties.region || feat.properties.Region || "";
      feat.properties.is_m0_red = isM0Red;
      feat.properties.m0_alerta = isM0Red ? "ROJO" : "NORMAL";
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

  const lookupEntry = communeH3Lookup[cleanName] || (cleanCod ? communeH3Lookup[cleanCod] : null);
  const h7Ids = lookupEntry ? lookupEntry.h7_ids : [];
  const h8Ids = lookupEntry ? lookupEntry.h8_ids : [];

  if (map.getLayer("comunas-fill")) {
    map.setFilter("comunas-fill", ["==", ["downcase", ["get", "comuna"]], cleanName]);
  }
  if (map.getLayer("comunas-lines")) {
    map.setFilter("comunas-lines", ["==", ["downcase", ["get", "comuna"]], cleanName]);
  }
  if (map.getLayer("comunas-m0-fill")) {
    map.setFilter("comunas-m0-fill", ["==", ["downcase", ["get", "comuna"]], cleanName]);
  }
  if (map.getLayer("comunas-m0-lines")) {
    map.setFilter("comunas-m0-lines", ["==", ["downcase", ["get", "comuna"]], cleanName]);
  }

  if (h7Ids.length > 0) {
    if (map.getLayer("h3-res7-fill-red")) {
      map.setFilter("h3-res7-fill-red", ["in", ["get", "h3_id"], ["literal", h7Ids]]);
    }
    if (map.getLayer("h3-res7-lines-red")) {
      map.setFilter("h3-res7-lines-red", ["in", ["get", "h3_id"], ["literal", h7Ids]]);
    }
    if (map.getLayer("h3-res7-fill-yellow")) {
      map.setFilter("h3-res7-fill-yellow", ["in", ["get", "h3_id"], ["literal", h7Ids]]);
    }
    if (map.getLayer("h3-res7-lines-yellow")) {
      map.setFilter("h3-res7-lines-yellow", ["in", ["get", "h3_id"], ["literal", h7Ids]]);
    }
  }

  if (h8Ids.length > 0 && map.getLayer("alert-heatmap")) {
    map.setFilter("alert-heatmap", ["in", ["get", "h3_id"], ["literal", h8Ids]]);
  }

  if (map.getLayer("fires-points") || map.getLayer("fires-all-circles")) {
    if (map.getLayer("fires-all-circles")) {
      map.setFilter("fires-all-circles", ["==", ["downcase", ["get", "comuna"]], cleanName]);
    }
    if (map.getLayer("fires-circles")) {
      map.setFilter("fires-circles", ["all", [">=", ["get", "area_ha"], 200], ["==", ["downcase", ["get", "comuna"]], cleanName]]);
    }
    if (map.getLayer("fires-heatmap")) {
      map.setFilter("fires-heatmap", ["==", ["downcase", ["get", "comuna"]], cleanName]);
    }
  }

  const btnReset = document.getElementById("btn-reset-view");
  if (btnReset) btnReset.classList.remove("hidden");
}

function resetCommuneFilter(flyBackToEvent = true) {
  selectedCommuneFilter = null;

  if (map.getLayer("comunas-fill")) map.setFilter("comunas-fill", null);
  if (map.getLayer("comunas-lines")) map.setFilter("comunas-lines", null);
  if (map.getLayer("comunas-m0-fill")) map.setFilter("comunas-m0-fill", null);
  if (map.getLayer("comunas-m0-lines")) map.setFilter("comunas-m0-lines", null);

  if (map.getLayer("h3-res7-fill-red")) map.setFilter("h3-res7-fill-red", ["==", ["get", "alerta"], "ROJO"]);
  if (map.getLayer("h3-res7-lines-red")) map.setFilter("h3-res7-lines-red", ["==", ["get", "alerta"], "ROJO"]);
  if (map.getLayer("h3-res7-fill-yellow")) map.setFilter("h3-res7-fill-yellow", ["==", ["get", "alerta"], "AMARILLO"]);
  if (map.getLayer("h3-res7-lines-yellow")) map.setFilter("h3-res7-lines-yellow", ["==", ["get", "alerta"], "AMARILLO"]);

  if (map.getLayer("alert-heatmap")) map.setFilter("alert-heatmap", null);
  if (map.getLayer("fires-all-circles")) map.setFilter("fires-all-circles", null);
  if (map.getLayer("fires-circles")) map.setFilter("fires-circles", [">=", ["get", "area_ha"], 200]);
  if (map.getLayer("fires-heatmap")) map.setFilter("fires-heatmap", null);

  const btnReset = document.getElementById("btn-reset-view");
  if (btnReset) btnReset.classList.add("hidden");

  if (flyBackToEvent && EVENT_CENTERS[activeEventDate]) {
    const ev = EVENT_CENTERS[activeEventDate];
    map.flyTo({ center: ev.center, zoom: ev.zoom, speed: 1.2, duration: 1000 });
  }
}

function calculateBBox(feature) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  const processCoords = (coords) => {
    if (typeof coords[0] === 'number') {
      const [x, y] = coords;
      if (x < minX) minX = x;
      if (x > maxX) maxX = x;
      if (y < minY) minY = y;
      if (y > maxY) maxY = y;
    } else {
      coords.forEach(processCoords);
    }
  };
  processCoords(feature.geometry.coordinates);
  return [[minX, minY], [maxX, maxY]];
}

// 6. CONTROLADOR DE METODOLOGÍAS Y COMPARACIÓN (BR-HR vs M0)
function aplicarModoModelo(mode) {
  currentModelMode = mode;

  // Actualizar botones de UI
  const btnBrHr = document.getElementById("btn-model-brhr");
  const btnM0 = document.getElementById("btn-model-m0");
  const btnBoth = document.getElementById("btn-model-both");
  const badge = document.getElementById("model-desc-badge");
  const chkBrHr = document.getElementById("layer-comunas");
  const chkM0 = document.getElementById("layer-comunas-m0");

  if (btnBrHr) btnBrHr.classList.toggle("active", mode === "BR_HR");
  if (btnM0) btnM0.classList.toggle("active", mode === "M0");
  if (btnBoth) btnBoth.classList.toggle("active", mode === "BOTH");

  if (mode === "BR_HR") {
    if (map.getLayer("comunas-fill")) map.setLayoutProperty("comunas-fill", "visibility", "visible");
    if (map.getLayer("comunas-lines")) map.setLayoutProperty("comunas-lines", "visibility", "visible");
    if (map.getLayer("comunas-m0-fill")) map.setLayoutProperty("comunas-m0-fill", "visibility", "none");
    if (map.getLayer("comunas-m0-lines")) map.setLayoutProperty("comunas-m0-lines", "visibility", "none");
    if (chkBrHr) chkBrHr.checked = true;
    if (chkM0) chkM0.checked = false;
    if (badge) badge.innerText = "Mostrando BR-HR 2026: Probabilidad continua con alertas rojas y amarillas preventivas.";
  } else if (mode === "M0") {
    if (map.getLayer("comunas-fill")) map.setLayoutProperty("comunas-fill", "visibility", "none");
    if (map.getLayer("comunas-lines")) map.setLayoutProperty("comunas-lines", "visibility", "none");
    if (map.getLayer("comunas-m0-fill")) map.setLayoutProperty("comunas-m0-fill", "visibility", "visible");
    if (map.getLayer("comunas-m0-lines")) map.setLayoutProperty("comunas-m0-lines", "visibility", "visible");
    if (chkBrHr) chkBrHr.checked = false;
    if (chkM0) chkM0.checked = true;
    if (badge) badge.innerText = "Mostrando M0 Original CONAF: Regla rígida binaria (≥30% combustible). Sin alerta preventiva.";
  } else if (mode === "BOTH") {
    if (map.getLayer("comunas-fill")) map.setLayoutProperty("comunas-fill", "visibility", "visible");
    if (map.getLayer("comunas-lines")) map.setLayoutProperty("comunas-lines", "visibility", "visible");
    if (map.getLayer("comunas-m0-fill")) map.setLayoutProperty("comunas-m0-fill", "visibility", "visible");
    if (map.getLayer("comunas-m0-lines")) map.setLayoutProperty("comunas-m0-lines", "visibility", "visible");
    if (chkBrHr) chkBrHr.checked = true;
    if (chkM0) chkM0.checked = true;
    if (badge) badge.innerText = "Comparador Superpuesto: M0 Original CONAF (borde grueso vino) vs BR-HR Calibrado.";
  }
}

// 7. Actualización de KPIs y Tabla
function updateKPIs(summary, communes, dateStr) {
  let redCount = 0;
  let yellowCount = 0;
  let m0RedCount = 0;

  communes.forEach(c => {
    if (c.alerta_comunal === "ALERTA ROJA COMUNAL" || (c.pct_superficie_roja || 0) >= 30) {
      redCount++;
    } else if (c.alerta_comunal === "ALERTA AMARILLA COMUNAL" || (c.pct_superficie_amarilla || 0) >= 20 || (c.pct_superficie_roja || 0) >= 10) {
      yellowCount++;
    }
    if (c.is_m0_red === true) {
      m0RedCount++;
    }
  });

  const m0El = document.getElementById("kpi-m0-communes");
  if (m0El) m0El.innerText = m0RedCount;

  document.getElementById("kpi-red-communes").innerText = redCount;
  document.getElementById("kpi-yellow-communes").innerText = yellowCount;

  const countBrHrEl = document.getElementById("count-brhr-layer");
  if (countBrHrEl) countBrHrEl.innerText = (redCount + yellowCount);

  const countM0El = document.getElementById("count-m0-layer");
  if (countM0El) countM0El.innerText = m0RedCount;

  if (summary && summary.pct_superficie_combustible_en_riesgo !== undefined) {
    document.getElementById("kpi-risk-pct").innerText = `${summary.pct_superficie_combustible_en_riesgo} %`;
  } else if (summary && summary.red_alert_percentage !== undefined) {
    document.getElementById("kpi-risk-pct").innerText = `${summary.red_alert_percentage} %`;
  } else if (summary && summary.pct_territorio_rojo !== undefined) {
    document.getElementById("kpi-risk-pct").innerText = `${summary.pct_territorio_rojo} %`;
  }
}

function renderCommunesTable(communes) {
  const tbody = document.getElementById("communes-tbody");
  tbody.innerHTML = "";

  const sorted = [...communes].sort((a, b) => {
    // Si M0 está seleccionado, ordenar por M0 primero
    if (currentModelMode === "M0") {
      if (a.is_m0_red && !b.is_m0_red) return -1;
      if (!a.is_m0_red && b.is_m0_red) return 1;
    }
    return (b.pct_superficie_roja || 0) - (a.pct_superficie_roja || 0);
  });

  sorted.forEach(com => {
    const tr = document.createElement("tr");
    const isRed = com.alerta_comunal === "ALERTA ROJA COMUNAL" || (com.pct_superficie_roja || 0) >= 30;
    const isYellow = com.alerta_comunal === "ALERTA AMARILLA COMUNAL" || (!isRed && ((com.pct_superficie_roja || 0) >= 10 || (com.pct_superficie_amarilla || 0) >= 20));
    const badgeClass = isRed ? "rojo" : (isYellow ? "amarillo" : "verde");
    const badgeText = isRed ? "ROJA" : (isYellow ? "AMARILLA" : "NORMAL");

    const m0Badge = com.is_m0_red
      ? `<span class="badge-m0-red">ROJO</span>`
      : `<span class="badge-m0-none">—</span>`;

    tr.innerHTML = `
      <td><strong>${com.comuna}</strong></td>
      <td><small>${com.region ? com.region.replace("Región de", "").replace("Región del", "").replace("Región de los", "").trim() : ""}</small></td>
      <td class="text-center">${m0Badge}</td>
      <td><strong>${(com.pct_superficie_roja || 0).toFixed(1)}%</strong></td>
      <td><span class="badge-alert ${badgeClass}">${badgeText}</span></td>
    `;

    tr.addEventListener("click", () => {
      openCommuneDetail(com);
      filterByCommune(com.comuna, com.codcom);
    });

    tbody.appendChild(tr);
  });
}

// 8. Interacciones y Clics
function setupMapInteractions() {
  const handleCommuneClick = (e) => {
    if (!e.features || e.features.length === 0) return;
    const props = e.features[0].properties;
    const comName = props.comuna || props.Comuna;
    const codcom = props.cod_comuna || props.codcom;

    openCommuneDetail({
      comuna: comName,
      region: props.region_name || props.region || props.Region,
      pct_superficie_roja: props.pct_rojo,
      pct_superficie_amarilla: props.pct_amarillo,
      total_hexagons: props.total_h3,
      red_hexagons: props.red_h3,
      alerta_comunal: props.alerta,
      is_m0_red: props.is_m0_red
    });

    filterByCommune(comName, codcom);
  };

  map.on("click", "comunas-fill", handleCommuneClick);
  map.on("click", "comunas-m0-fill", handleCommuneClick);

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
  map.on("mouseenter", "comunas-m0-fill", () => map.getCanvas().style.cursor = "pointer");
  map.on("mouseleave", "comunas-m0-fill", () => map.getCanvas().style.cursor = "");
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

  const m0StatusHtml = com.is_m0_red
    ? `<span class="badge-alert rojo">🔴 ALERTA ROJA (Oficial CONAF)</span>`
    : `<span class="badge-alert verde">⚪ SIN ALERTA (Falso Negativo / No Detectado)</span>`;

  showInspector(`🏛️ Detalle Comunal: ${com.comuna}`, `
    <p><strong>Región:</strong> ${com.region || ''}</p>
    <hr style="margin: 6px 0; border: none; border-top: 1px solid #e2e8f0;" />
    <p><strong>🏛️ M0 Original CONAF:</strong> ${m0StatusHtml}</p>
    <p><strong>🚀 BR-HR Calibrado 2026:</strong> <span class="badge-alert ${badgeClass}">${com.alerta_comunal || (isRed ? 'ALERTA ROJA' : (isYellow ? 'ALERTA AMARILLA' : 'NORMAL'))}</span></p>
    <hr style="margin: 6px 0; border: none; border-top: 1px solid #e2e8f0;" />
    <p><strong>Superficie en Botón Rojo:</strong> <strong>${(com.pct_superficie_roja || 0).toFixed(1)}%</strong></p>
    <p><strong>Total Hexágonos H3:</strong> ${com.total_hexagons || com.total_cells || 0}</p>
    <p><strong>Hexágonos en Alerta Roja:</strong> ${com.red_hexagons || com.red_cells_count || 0}</p>
  `);
}

// 9. Event Listeners
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

  // Botones del Selector de Metodología
  const btnBrHr = document.getElementById("btn-model-brhr");
  const btnM0 = document.getElementById("btn-model-m0");
  const btnBoth = document.getElementById("btn-model-both");

  if (btnBrHr) btnBrHr.addEventListener("click", () => { aplicarModoModelo("BR_HR"); renderCommunesTable(communesList); });
  if (btnM0) btnM0.addEventListener("click", () => { aplicarModoModelo("M0"); renderCommunesTable(communesList); });
  if (btnBoth) btnBoth.addEventListener("click", () => { aplicarModoModelo("BOTH"); renderCommunesTable(communesList); });

  // Botón Limpiar Filtro Comunal
  const btnReset = document.getElementById("btn-reset-view");
  if (btnReset) {
    btnReset.addEventListener("click", () => {
      resetCommuneFilter(true);
    });
  }

  // 1. Capa Comunas BR-HR
  document.getElementById("layer-comunas").addEventListener("change", (e) => {
    const vis = e.target.checked ? "visible" : "none";
    if (map.getLayer("comunas-fill")) map.setLayoutProperty("comunas-fill", "visibility", vis);
    if (map.getLayer("comunas-lines")) map.setLayoutProperty("comunas-lines", "visibility", vis);
  });

  // 2. Capa Comunas M0 Original
  const chkM0 = document.getElementById("layer-comunas-m0");
  if (chkM0) {
    chkM0.addEventListener("change", (e) => {
      const vis = e.target.checked ? "visible" : "none";
      if (map.getLayer("comunas-m0-fill")) map.setLayoutProperty("comunas-m0-fill", "visibility", vis);
      if (map.getLayer("comunas-m0-lines")) map.setLayoutProperty("comunas-m0-lines", "visibility", vis);
    });
  }

  // 3. Hexágonos Res 7 Rojos
  document.getElementById("layer-h3-red").addEventListener("change", (e) => {
    const vis = e.target.checked ? "visible" : "none";
    if (map.getLayer("h3-res7-fill-red")) map.setLayoutProperty("h3-res7-fill-red", "visibility", vis);
    if (map.getLayer("h3-res7-lines-red")) map.setLayoutProperty("h3-res7-lines-red", "visibility", vis);
  });

  // 4. Hexágonos Res 7 Amarillos
  document.getElementById("layer-h3-yellow").addEventListener("change", (e) => {
    const vis = e.target.checked ? "visible" : "none";
    if (map.getLayer("h3-res7-fill-yellow")) map.setLayoutProperty("h3-res7-fill-yellow", "visibility", vis);
    if (map.getLayer("h3-res7-lines-yellow")) map.setLayoutProperty("h3-res7-lines-yellow", "visibility", vis);
  });

  // 5. Mapa de Calor de Alerta Botón Rojo
  toggleLayerCheckbox("layer-alert-kde", "alert-heatmap");

  // 6. Capa Satelital NASA FIRMS en Vivo
  const firmsChk = document.getElementById("layer-firms");
  if (firmsChk) {
    firmsChk.addEventListener("change", (e) => {
      if (map.getLayer("firms-points-layer")) {
        map.setLayoutProperty("firms-points-layer", "visibility", e.target.checked ? "visible" : "none");
      }
    });
  }

  // 7. Mapa de Calor Satelital NASA FIRMS
  toggleLayerCheckbox("layer-firms-kde", "firms-heatmap");

  // 8. Focos de Incendio y KDE de Incendios Observados
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
