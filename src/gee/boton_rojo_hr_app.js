/**
 * src/gee/boton_rojo_hr_app.js — Aplicación Web y Script Interactivo para Google Earth Engine Code Editor.
 *
 * Plataforma institucional de visualización interactiva de Botón Rojo de Alta Resolución (BR-HR).
 * Título: "Botón Rojo Chile - Versión 2026"
 *
 * Incluye:
 * - Capa de Límites Comunales de Chile (Asset: projects/boton-rojo-chile/assets/comunas_chile).
 * - Cobertura de Combustibles Dynamic World corregida (carga rápida sin timeouts).
 * - Vista inicial focalizada: Botón Rojo Calibrado (M1), Alerta Amarilla, Grandes Incendios y Megaincendios.
 * - Leyendas dinámicas sincronizadas con el panel nativo de Layers y Scroll Vertical.
 *
 * Instrucciones: Copiar y pegar este script en https://code.earthengine.google.com/ y pulsar Run.
 */

// 1. Límite territorial oficial y Límites Comunales de Chile
var countries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017");
var chile = countries.filter(ee.Filter.eq("country_na", "Chile"));

var COMUNAS_ASSET = "projects/boton-rojo-chile/assets/comunas_chile";
var coleccionComunas;
try {
  coleccionComunas = ee.FeatureCollection(COMUNAS_ASSET);
} catch(e) {
  coleccionComunas = chile;
}

Map.centerObject(ee.Geometry.Point([-72.0, -36.5]), 7);
Map.setOptions("HYBRID");

// 2. Modelo de Elevación y Sombra SRTM 30m
var srtm = ee.Image("USGS/SRTMGL1_003").clip(chile);
var terrain = ee.Algorithms.Terrain(srtm);
var slopeRad = terrain.select("slope").multiply(Math.PI / 180.0);
var aspectRad = terrain.select("aspect").multiply(Math.PI / 180.0);
var azimuthRad = 313.0 * (Math.PI / 180.0);
var altitudeRad = 60.0 * (Math.PI / 180.0);

var hs = slopeRad.cos().multiply(Math.sin(altitudeRad))
  .add(slopeRad.sin().multiply(Math.cos(altitudeRad)).multiply(aspectRad.subtract(azimuthRad).cos()))
  .multiply(255.0)
  .rename("hillshade");

// 3. Cobertura de Combustibles Base (ESA WorldCover 10m)
var worldCover = ee.ImageCollection("ESA/WorldCover/v100").first().clip(chile);
var fuelMask = worldCover.eq(10).or(worldCover.eq(20)).or(worldCover.eq(30)).or(worldCover.eq(40)).or(worldCover.eq(90));

var fuelClassified = worldCover.remap(
  [10, 20, 30, 40, 90],
  [1, 2, 3, 4, 5]
).updateMask(fuelMask);

// 4. Carga del Asset de Incendios Históricos CONAF
var ASSET_PATH = "projects/boton-rojo-chile/assets/incendios_conaf_historico";
var tablaCruda = ee.FeatureCollection(ASSET_PATH);

function asignarPuntoGeometria(feat) {
  var lon = feat.getNumber("lon");
  var lat = feat.getNumber("lat");
  var area = ee.Number(feat.get("area_ha"));
  var pt = ee.Geometry.Point([lon, lat]);
  var weight = area.add(1.0).sqrt().max(1.0);
  return feat.setGeometry(pt).set({
    "weight": weight,
    "area_val": area
  });
}

var coleccionIncendios = tablaCruda.map(asignarPuntoGeometria);

/**
 * Función principal para procesar y cargar las capas de la fecha seleccionada.
 */
function cargarFecha(fechaStr) {
  Map.layers().reset();

  var isHistorical = (fechaStr !== "HOY");
  var tempC, rhPct, windKmh;
  var startDate, endDate;

  if (isHistorical) {
    startDate = ee.Date(fechaStr);
    endDate = startDate.advance(1, "day");
    
    // Tarde en Chile (14:00 a 19:00 local = 17:00 a 22:00 UTC)
    var era5 = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY")
      .filterDate(startDate, endDate)
      .filter(ee.Filter.calendarRange(17, 22, "hour"));

    var era5Mean = era5.mean();
    tempC = era5Mean.select("temperature_2m").subtract(273.15).clip(chile).rename("temp_c");
    var dewC = era5Mean.select("dewpoint_temperature_2m").subtract(273.15);
    
    var vp = dewC.multiply(17.27).divide(dewC.add(237.3)).exp();
    var vps = tempC.multiply(17.27).divide(tempC.add(237.3)).exp();
    rhPct = ee.Image(100).multiply(vp).divide(vps).clamp(3, 100).clip(chile).rename("rh_pct");
    
    var uWind = era5Mean.select("u_component_of_wind_10m");
    var vWind = era5Mean.select("v_component_of_wind_10m");
    windKmh = uWind.hypot(vWind).multiply(3.6).clip(chile).rename("wind_kmh");
  } else {
    startDate = ee.Date(Date.now()).advance(-1, "year");
    endDate = ee.Date(Date.now());

    var gfs = ee.ImageCollection("NOAA/GFS0P25")
      .filterDate(ee.Date(Date.now()).advance(-2, "day"), ee.Date(Date.now()).advance(3, "day"))
      .sort("system:time_start", false).first();
    tempC = gfs.select("temperature_2m_above_ground").subtract(273.15).clip(chile).rename("temp_c");
    rhPct = gfs.select("relative_humidity_2m_above_ground").clip(chile).rename("rh_pct");
    var uWind = gfs.select("u_component_of_wind_10m_above_ground");
    var vWind = gfs.select("v_component_of_wind_10m_above_ground");
    windKmh = uWind.hypot(vWind).multiply(3.6).clip(chile).rename("wind_kmh");
  }

  // 1. Humedad del Combustible Fino Muerto (HCFM) y Probabilidad de Ignición Continua
  var hcfm = rhPct.multiply(0.262).subtract(tempC.multiply(0.00982)).add(0.297374).rename("hcfm");
  var piContinua = ee.Image(100).subtract(hcfm.multiply(7.5)).add(tempC.multiply(0.5)).clamp(5, 95).updateMask(fuelMask);

  // 2. Umbrales Calibrados de Alerta
  var botonRojoM1 = hcfm.lte(6.5).and(windKmh.gte(16.0)).and(fuelMask);
  var botonRojoM0 = hcfm.lte(5.0).and(windKmh.gte(18.0)).and(fuelMask);
  var alertaAmarilla = hcfm.lte(7.0).and(windKmh.gte(14.0)).and(fuelMask);

  var capaM1Visible = botonRojoM1.updateMask(botonRojoM1.eq(1));
  var capaM0Visible = botonRojoM0.updateMask(botonRojoM0.eq(1));
  var capaAmarillaVisible = alertaAmarilla.updateMask(alertaAmarilla.eq(1));

  // 3. Capa Dynamic World Optimizada (Carga en < 1 segundo)
  var dwCol = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
    .filterDate(startDate.advance(-1, "month"), startDate.advance(1, "month"))
    .select("label");
  var dwMode = dwCol.reduce(ee.Reducer.mode()).clip(chile);
  var dwRemapped = dwMode.remap([1, 5, 2, 4, 3], [1, 2, 3, 4, 5], 0);
  var dwVisible = dwRemapped.updateMask(dwRemapped.gt(0));

  // 4. AGREGAR CAPAS AL MAPA
  
  // A. Límites Comunales de Chile
  var comunasStyle = coleccionComunas.style({
    color: "ffffff",
    fillColor: "00000000",
    width: 1.2
  });
  Map.addLayer(comunasStyle, {}, "🏛️ Límites Comunales (Chile)", true);

  // B. Capas Meteorológicas (Inactivas al inicio)
  Map.addLayer(tempC, {min: 15, max: 38, palette: ["#005f73", "#94d2bd", "#ee9b00", "#ca6702", "#ae2012"]}, "🌡️ Temperatura 14-18h (°C)", false);
  Map.addLayer(rhPct, {min: 10, max: 70, palette: ["#780000", "#c1121f", "#fdf0d5", "#669bbc", "#003049"]}, "💧 Humedad Relativa (%)", false);
  Map.addLayer(windKmh, {min: 5, max: 40, palette: ["#edf2f4", "#8d99ae", "#2b2d42", "#d90429"]}, "💨 Viento 10m (km/h)", false);
  Map.addLayer(hcfm.updateMask(fuelMask), {min: 2, max: 15, palette: ["#d90429", "#f77f00", "#fcbf49", "#eae2b7", "#2a9d8f"]}, "🌾 Humedad Combustible HCFM (%)", false);
  Map.addLayer(hs, {min: 0, max: 255}, "⛰️ Hillshade SRTM 30m", false);
  
  // C. Capas de Vegetación (Inactivas al inicio)
  Map.addLayer(fuelClassified, {
    min: 1, max: 5,
    palette: ["#1b4332", "#52b788", "#e9c46a", "#f4a261", "#48cae4"]
  }, "🌲 Tipos de Vegetación (ESA 10m)", false);

  Map.addLayer(dwVisible, {
    min: 1, max: 5,
    palette: ["#1b4332", "#52b788", "#e9c46a", "#f4a261", "#48cae4"]
  }, "🛰️ Vegetación Dynamic World (10m)", false);

  Map.addLayer(piContinua, {min: 25, max: 80, palette: ["#2b9348", "#80b918", "#d4d700", "#ffff3f", "#ffaa00", "#ff4800", "#d00000"]}, "🔥 Prob. Ignición Continua (0-100%)", false);
  Map.addLayer(capaM0Visible, {palette: ["#ff9100"]}, "🟠 Botón Rojo Baseline (M0 CONAF)", false);

  // D. CAPAS DE ALERTA ACTIVAS AL INICIO
  Map.addLayer(capaAmarillaVisible, {palette: ["#ffea00"]}, "🟡 Alerta Amarilla Preventiva", true);
  Map.addLayer(capaM1Visible, {palette: ["#d90429"]}, "🔴 Botón Rojo Calibrado (M1 BR-HR)", true);

  // 5. MAPA DE CALOR CONTINUO KERNEL Y FOCOS DE INCENDIO
  if (isHistorical) {
    var incendiosDelDia = coleccionIncendios.filter(ee.Filter.eq("date", fechaStr));
    
    var canvas = srtm.multiply(0).rename("kde");
    var pointRaster = canvas.paint({featureCollection: incendiosDelDia, color: "weight"});
    var gaussianKernel = ee.Kernel.gaussian({radius: 35000, sigma: 14000, units: "meters"});
    var kdeContinuous = pointRaster.convolve(gaussianKernel).clip(chile);
    var kdeMasked = kdeContinuous.updateMask(kdeContinuous.gt(0.0005));

    Map.addLayer(kdeMasked, {
      min: 0.001, max: 0.08,
      palette: ["#001219", "#005f73", "#0a9396", "#94d2bd", "#e9d8a6", "#ee9b00", "#ca6702", "#bb3e03", "#ae2012", "#9b2226", "#ffffff"]
    }, "💥 Mapa de Calor Incendios (KDE)", false);

    var mega = incendiosDelDia.filter(ee.Filter.gte("area_ha", 1000));
    var large = incendiosDelDia.filter(ee.Filter.and(ee.Filter.gte("area_ha", 100), ee.Filter.lt("area_ha", 1000)));
    var med = incendiosDelDia.filter(ee.Filter.and(ee.Filter.gte("area_ha", 10), ee.Filter.lt("area_ha", 100)));
    var small = incendiosDelDia.filter(ee.Filter.lt("area_ha", 10));

    Map.addLayer(small.draw({color: "ffff00", pointRadius: 4, strokeWidth: 1}), {}, "🟡 Foco Menor (< 10 ha)", false);
    Map.addLayer(med.draw({color: "ff7700", pointRadius: 7, strokeWidth: 2}), {}, "🟠 Incendio Mediano (10 - 100 ha)", false);

    // GRANDES Y MEGAINCENDIOS ACTIVOS AL INICIO
    Map.addLayer(large.draw({color: "ff0000", pointRadius: 10, strokeWidth: 2}), {}, "🔴 Gran Incendio (100 - 1.000 ha)", true);
    Map.addLayer(mega.draw({color: "ffffff", pointRadius: 14, strokeWidth: 3}), {}, "🟣 Megaincendio (> 1.000 ha)", true);

    incendiosDelDia.size().evaluate(function(totalCount) {
      statusLabel.setValue("📅 Fecha: " + fechaStr + " | 🔥 Incendios CONAF: " + totalCount);
    });
  } else {
    statusLabel.setValue("📅 Fecha: HOY (Pronóstico GFS en tiempo real)");
  }

  actualizarLeyendasDesdeLayers();
}

/**
 * Inspecciona las capas actualmente activas en el panel de Layers nativo de GEE
 * y genera dinámicamente las leyendas correspondientes.
 */
function actualizarLeyendasDesdeLayers() {
  legendContainer.clear();
  var headerPanel = ui.Panel({
    widgets: [
      ui.Label({value: "📋 Leyendas Activas:", style: {fontWeight: "bold", fontSize: "12px", color: "#1d3557", margin: "4px 0px"}}),
      ui.Button({label: "🔄 Actualizar Leyendas", onClick: actualizarLeyendasDesdeLayers, style: {margin: "0px 0px 0px 8px"}})
    ],
    layout: ui.Panel.Layout.flow("horizontal")
  });
  legendContainer.add(headerPanel);

  var anyActive = false;
  var layers = Map.layers();

  for (var i = 0; i < layers.length(); i++) {
    var layer = layers.get(i);
    if (!layer.getShown()) continue;

    anyActive = true;
    var name = layer.getName();

    if (name.indexOf("Límites Comunales") !== -1) {
      legendContainer.add(ui.Label({value: "🏛️ Límites Comunales:", style: {fontWeight: "bold", color: "#1d3557", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Líneas blancas de división político-administrativa comunal.", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Botón Rojo Calibrado") !== -1) {
      legendContainer.add(ui.Label({value: "🔴 Botón Rojo Calibrado (M1):", style: {fontWeight: "bold", color: "#d90429", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Máxima severidad. Probabilidad crítica de propagación extrema.", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Alerta Amarilla") !== -1) {
      legendContainer.add(ui.Label({value: "🟡 Alerta Amarilla Preventiva:", style: {fontWeight: "bold", color: "#bfa004", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Zona de amortiguación y advertencia preventiva.", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Baseline") !== -1) {
      legendContainer.add(ui.Label({value: "🟠 Botón Rojo Baseline (M0 CONAF):", style: {fontWeight: "bold", color: "#ff9100", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Criterio rígido tradicional CONAF.", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Megaincendio") !== -1) {
      legendContainer.add(ui.Label({value: "🟣 Megaincendios (> 1.000 ha):", style: {fontWeight: "bold", color: "#6a040f", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Círculos gigantes (blanco/púrpura). Focos de devastación extrema.", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Gran Incendio") !== -1) {
      legendContainer.add(ui.Label({value: "🔴 Gran Incendio (100 - 1.000 ha):", style: {fontWeight: "bold", color: "#d00000", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Círculos rojos. Incendios mayores de rápida expansión.", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Incendio Mediano") !== -1 || name.indexOf("Foco Menor") !== -1) {
      legendContainer.add(ui.Label({value: "🎯 " + name, style: {fontWeight: "bold", fontSize: "11px"}}));
    } else if (name.indexOf("Mapa de Calor") !== -1) {
      legendContainer.add(ui.Label({value: "💥 Mapa de Calor Incendios (KDE):", style: {fontWeight: "bold", color: "#bb3e03", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Densidad continua: Azul (baja) -> Naranja -> Blanco (máxima concentración).", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Vegetación") !== -1 || name.indexOf("Dynamic World") !== -1) {
      legendContainer.add(ui.Label({value: "🌲 Vegetación Combustible (10m):", style: {fontWeight: "bold", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "🌲 Verde Oscuro: Bosques / Plantaciones", style: {fontSize: "10px", color: "#1b4332"}}));
      legendContainer.add(ui.Label({value: "🌿 Verde Oliva: Matorrales", style: {fontSize: "10px", color: "#52b788"}}));
      legendContainer.add(ui.Label({value: "🌾 Amarillo: Pastizal Fino", style: {fontSize: "10px", color: "#c89f36"}}));
      legendContainer.add(ui.Label({value: "🚜 Naranja: Cultivos / Rastrojos", style: {fontSize: "10px", color: "#e76f51"}}));
      legendContainer.add(ui.Label({value: "💧 Cian: Humedales", style: {fontSize: "10px", color: "#2a9d8f"}}));
    } else if (name.indexOf("Temperatura") !== -1) {
      legendContainer.add(ui.Label({value: "🌡️ Temperatura (°C):", style: {fontWeight: "bold", color: "#ae2012", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Rango: 15 °C (Azul/Cian) -> 38 °C (Rojo oscuro).", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Humedad Relativa") !== -1) {
      legendContainer.add(ui.Label({value: "💧 Humedad Relativa (%):", style: {fontWeight: "bold", color: "#003049", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Rango: 10 % (Rojo seco) -> 70 % (Azul húmedo).", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Viento") !== -1) {
      legendContainer.add(ui.Label({value: "💨 Viento (km/h):", style: {fontWeight: "bold", color: "#2b2d42", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Rango: 5 km/h (Gris) -> 40 km/h (Rojo viento).", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("HCFM") !== -1) {
      legendContainer.add(ui.Label({value: "🌾 Humedad Combustible HCFM (%):", style: {fontWeight: "bold", color: "#d90429", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Rango: 2 % (Rojo crítico) -> 15 % (Verde seguro).", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Prob. Ignición") !== -1) {
      legendContainer.add(ui.Label({value: "🔥 Probabilidad de Ignición Continua:", style: {fontWeight: "bold", color: "#d00000", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Rango: 25 % (Verde) -> 80 % (Rojo extremo).", style: {fontSize: "10px", color: "#555"}}));
    }
  }

  if (!anyActive) {
    legendContainer.add(ui.Label({value: "No hay capas activas. Activa una capa en el menú Layers de la derecha.", style: {fontSize: "10px", color: "#888"}}));
  }
}

// 6. Inspector de Clic Interactivo
Map.onClick(function(coords) {
  var pt = ee.Geometry.Point([coords.lon, coords.lat]);
  
  // Buscar comuna bajo el cursor
  var sampleComuna = coleccionComunas.filterBounds(pt).first();
  // Buscar incendio cercano
  var sampleFires = coleccionIncendios.filterBounds(pt.buffer(8000)).limit(1);

  var merged = ee.Dictionary({
    "comuna": sampleComuna,
    "fuego": sampleFires
  });

  merged.evaluate(function(res) {
    inspectorPanel.clear();
    inspectorPanel.add(ui.Label({value: "📍 Inspector de Punto / Territorio", style: {fontWeight: "bold", fontSize: "12px"}}));
    inspectorPanel.add(ui.Label({value: "Coordenadas: " + coords.lat.toFixed(4) + ", " + coords.lon.toFixed(4), style: {fontSize: "11px"}}));

    if (res && res.comuna && res.comuna.properties) {
      var cProps = res.comuna.properties;
      inspectorPanel.add(ui.Label({value: "🏛️ Comuna: " + (cProps.comuna || cProps.Comuna || "Chile") + " (" + (cProps.region || cProps.Region || "") + ")", style: {fontWeight: "bold", fontSize: "11px", color: "#1d3557"}}));
    }

    if (res && res.fuego && res.fuego.features && res.fuego.features.length > 0) {
      var fProps = res.fuego.features[0].properties;
      inspectorPanel.add(ui.Label({value: "🔥 INCENDIO CERCANO:", style: {fontWeight: "bold", color: "#d90429", fontSize: "12px"}}));
      inspectorPanel.add(ui.Label({value: "Foco: " + fProps.comuna + " | Superficie: " + Number(fProps.area_ha).toFixed(1) + " ha", style: {fontSize: "11px"}}));
      var tipo = fProps.area_ha >= 1000 ? "🟣 MEGAINCENDIO" : (fProps.area_ha >= 100 ? "🔴 GRAN INCENDIO" : (fProps.area_ha >= 10 ? "🟠 MEDIANO" : "🟡 MENOR"));
      inspectorPanel.add(ui.Label({value: "Severidad: " + tipo, style: {fontWeight: "bold", fontSize: "11px"}}));
    }
  });
});

// 7. Panel Principal de Interfaz
var panel = ui.Panel({
  style: {
    position: "top-left",
    padding: "12px",
    width: "350px",
    maxHeight: "88vh",
    backgroundColor: "#ffffff"
  }
});

panel.add(ui.Label({
  value: "🔥 Botón Rojo Chile - Versión 2026",
  style: {fontWeight: "bold", fontSize: "15px", color: "#d90429"}
}));

panel.add(ui.Label({value: "1. Selecciona un Evento Crítico:", style: {fontWeight: "bold", margin: "4px 0px 2px 0px"}}));

var dateSelect = ui.Select({
  items: [
    {label: "🔴 2023-02-03 (Megaincendios Biobío/Ñuble - 116.500 ha)", value: "2023-02-03"},
    {label: "🔴 2023-02-02 (Inicio Megatormenta 2023 - 151.800 ha)", value: "2023-02-02"},
    {label: "🔴 2024-02-02 (Megaincendio Viña del Mar/Quilpué)", value: "2024-02-02"},
    {label: "🔴 2017-01-20 (Tormenta Las Máquinas - 211.000 ha)", value: "2017-01-20"},
    {label: "🔴 2017-01-17 (O'Higgins / Maule - 62.000 ha)", value: "2017-01-17"},
    {label: "🔴 2020-02-09 (Ola de calor verano 2020 - 18.000 ha)", value: "2020-02-09"},
    {label: "🌐 Pronóstico Hoy (NOAA GFS en vivo)", value: "HOY"}
  ],
  placeholder: "Seleccionar evento...",
  value: "2023-02-03",
  onChange: function(val) {
    dateTextBox.setValue(val);
    cargarFecha(val);
  },
  style: {width: "95%"}
});
panel.add(dateSelect);

panel.add(ui.Label({value: "2. O escribe cualquier Fecha (2014-2024):", style: {margin: "8px 0px 2px 0px", fontWeight: "bold"}}));

var dateTextBox = ui.Textbox({placeholder: "AAAA-MM-DD", value: "2023-02-03", style: {width: "60%"}});
var dateButton = ui.Button({
  label: "🔍 Cargar",
  onClick: function() {
    var val = dateTextBox.getValue();
    if (val) cargarFecha(val.trim());
  },
  style: {margin: "0px 0px 0px 6px"}
});

var customDatePanel = ui.Panel({widgets: [dateTextBox, dateButton], layout: ui.Panel.Layout.flow("horizontal")});
panel.add(customDatePanel);

var statusLabel = ui.Label({style: {fontWeight: "bold", color: "#1d3557", margin: "6px 0px 6px 0px", fontSize: "12px"}});
panel.add(statusLabel);

panel.add(ui.Label({
  value: "💡 Activa/desactiva capas en el menú 'Layers' (arriba derecha) y haz clic en 'Actualizar Leyendas'.",
  style: {fontSize: "11px", color: "#555", margin: "4px 0px 6px 0px"}
}));

var inspectorPanel = ui.Panel({style: {margin: "4px 0px", padding: "6px", backgroundColor: "#f8f9fa"}});
panel.add(inspectorPanel);

var legendContainer = ui.Panel({
  style: {
    margin: "6px 0px",
    padding: "8px",
    backgroundColor: "#fdfdfd",
    border: "1px solid #e9ecef"
  }
});
panel.add(legendContainer);

Map.add(panel);

// Carga Inicial con las capas solicitadas
cargarFecha("2023-02-03");
