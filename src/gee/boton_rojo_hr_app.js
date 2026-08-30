/**
 * src/gee/boton_rojo_hr_app.js — Aplicación Web y Script Interactivo para Google Earth Engine Code Editor.
 *
 * Plataforma institucional de visualización interactiva de Botón Rojo de Alta Resolución (BR-HR).
 * Título: "Botón Rojo Chile - Versión 2026"
 *
 * Incluye:
 * - Capa de Límites Comunales de Chile (Asset: projects/boton-rojo-chile/assets/comunas_chile).
 * - Monitoreo Satelital en Vivo: NASA FIRMS (MODIS y VIIRS 375m NRT).
 * - Cobertura de Combustibles Dynamic World y ESA WorldCover 10m.
 * - Vista inicial: Pronóstico Hoy (Tiempo Real / GFS + FIRMS) y Catálogo Multiescenario.
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

Map.centerObject(ee.Geometry.Point([-71.8, -36.0]), 6);
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
    endDate = startDate.advance(2, "day"); // Ventana completa de emergencia
    
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
    var gfs = ee.ImageCollection("NOAA/GFS0P25")
      .filterDate(ee.Date(Date.now()).advance(-24, "hour"), ee.Date(Date.now()))
      .limit(1, "system:time_start", false)
      .first();

    tempC = gfs.select("temperature_2m_above_ground").subtract(273.15).clip(chile).rename("temp_c");
    rhPct = gfs.select("relative_humidity_2m_above_ground").clamp(3, 100).clip(chile).rename("rh_pct");
    
    var uGfs = gfs.select("u_component_of_wind_10m_above_ground");
    var vGfs = gfs.select("v_component_of_wind_10m_above_ground");
    windKmh = uGfs.hypot(vGfs).multiply(3.6).clip(chile).rename("wind_kmh");
    startDate = ee.Date(Date.now()).advance(-2, "day");
    endDate = ee.Date(Date.now());
  }

  // 1. Humedad de Combustible Fino Muerto (HCFM - Fórmula CONAF)
  var hcfm = rhPct.multiply(0.20)
    .add(ee.Image(100).subtract(tempC).multiply(0.05))
    .clamp(1.0, 30.0)
    .rename("hcfm");

  // 2. Probabilidad de Ignición Continua (PI Matriz CONAF)
  var piContinua = tempC.multiply(1.2)
    .add(ee.Image(100).subtract(rhPct).multiply(0.6))
    .add(windKmh.multiply(0.8))
    .subtract(hcfm.multiply(2.5))
    .clamp(0, 100)
    .rename("pi_continua");

  // 3. Reglas de Decisión Botón Rojo
  var condTemp = tempC.gte(20.0);
  var condRh = rhPct.lte(30.0);
  var condWind = windKmh.gte(20.0);
  var condHcfm = hcfm.lte(8.0);

  var botonRojoM0 = condTemp.and(condRh).and(condWind).and(condHcfm).and(fuelMask);
  var capaM0Visible = botonRojoM0.updateMask(botonRojoM0);

  var botonRojoM1 = piContinua.gte(60.0).and(fuelMask).and(hcfm.lte(10.0));
  var alertaAmarilla = piContinua.gte(40.0).and(piContinua.lt(60.0)).and(fuelMask);

  var capaM1Visible = botonRojoM1.updateMask(botonRojoM1);
  var capaAmarillaVisible = alertaAmarilla.updateMask(alertaAmarilla);

  // Dynamic World Vegetación
  var dwCol = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
    .filterBounds(chile)
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
  Map.addLayer(comunasStyle, {}, "🏛️ Comunas en Botón Rojo (346)", true);

  // B. Capas Meteorológicas (Inactivas al inicio)
  Map.addLayer(tempC, {min: 15, max: 38, palette: ["#005f73", "#94d2bd", "#ee9b00", "#ca6702", "#ae2012"]}, "🌡️ Temperatura 14-18h (°C)", false);
  Map.addLayer(rhPct, {min: 10, max: 70, palette: ["#780000", "#c1121f", "#fdf0d5", "#669bbc", "#003049"]}, "💧 Humedad Relativa (%)", false);
  Map.addLayer(windKmh, {min: 5, max: 40, palette: ["#edf2f4", "#8d99ae", "#2b2d42", "#d90429"]}, "💨 Viento 10m (km/h)", false);
  Map.addLayer(hcfm.updateMask(fuelMask), {min: 2, max: 15, palette: ["#d90429", "#f77f00", "#fcbf49", "#eae2b7", "#2a9d8f"]}, "🌾 Humedad Combustible HCFM (%)", false);
  Map.addLayer(hs, {min: 0, max: 255}, "⛰️ Hillshade SRTM 30m", false);
  
  // C. Capas de Vegetación
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
  Map.addLayer(capaAmarillaVisible, {palette: ["#ffea00"]}, "🟡 Alerta Amarilla Preventiva", false);
  Map.addLayer(capaM1Visible, {palette: ["#d90429"]}, "🔴 Botón Rojo Calibrado (M1 BR-HR)", false);

  // E. NASA FIRMS SATELITAL EN VIVO
  var firmsCol = ee.ImageCollection("FIRMS").filterBounds(chile).filterDate(startDate, endDate);
  if (firmsCol.size().getInfo() > 0) {
    var firmsT21 = firmsCol.select("T21").mosaic().clip(chile);
    var firmsMasked = firmsT21.updateMask(firmsT21.gte(305));
    Map.addLayer(firmsMasked, {min: 310, max: 400, palette: ["#ffe600", "#ff5500", "#ff0055", "#7209b7"]}, "🛰️ Anomalías Térmicas NASA FIRMS (VIIRS/MODIS)", false);
  }

  // F. MAPA DE CALOR CONTINUO KERNEL Y FOCOS DE INCENDIO CONAF
  if (isHistorical) {
    var incendiosDelDia = coleccionIncendios.filter(ee.Filter.eq("date", fechaStr));
    
    var canvas = srtm.multiply(0).rename("kde");
    var pointRaster = canvas.paint({featureCollection: incendiosDelDia, color: "weight"});
    var gaussianKernel = ee.Kernel.gaussian({radius: 30000, sigma: 12000, units: "meters"});
    var kdeContinuous = pointRaster.convolve(gaussianKernel).clip(chile);
    var kdeMasked = kdeContinuous.updateMask(kdeContinuous.gt(0.0005));

    Map.addLayer(kdeMasked, {
      min: 0.001, max: 0.08,
      palette: ["#001219", "#005f73", "#0a9396", "#94d2bd", "#e9d8a6", "#ee9b00", "#ca6702", "#bb3e03", "#ae2012", "#9b2226", "#ffffff"]
    }, "💥 Mapa de Calor Incendios CONAF (KDE)", false);

    var mega = incendiosDelDia.filter(ee.Filter.gte("area_ha", 1000));
    var large = incendiosDelDia.filter(ee.Filter.and(ee.Filter.gte("area_ha", 200), ee.Filter.lt("area_ha", 1000)));
    var allFires = incendiosDelDia;

    Map.addLayer(allFires.draw({color: "ffaa00", pointRadius: 3, strokeWidth: 1}), {}, "🔥 Todos los Focos de Incendio (CONAF)", false);
    Map.addLayer(large.draw({color: "ff0000", pointRadius: 6, strokeWidth: 2}), {}, "🔴 Gran Incendio (≥ 200 ha)", false);
    Map.addLayer(mega.draw({color: "7209b7", pointRadius: 8, strokeWidth: 2}), {}, "🟣 Megaincendio (≥ 1.000 ha)", false);

    incendiosDelDia.size().evaluate(function(totalCount) {
      statusLabel.setValue("📅 " + fechaStr + " | 🔥 CONAF: " + totalCount + " focos");
    });
  } else {
    statusLabel.setValue("📅 Pronóstico Hoy | 🌐 GFS + NASA FIRMS en Vivo");
  }

  actualizarLeyendas();
}

// 5. Generador de Leyendas Dinámicas
function actualizarLeyendas() {
  legendContainer.clear();
  legendContainer.add(ui.Label({value: "📋 Leyendas de Capas Activas", style: {fontWeight: "bold", fontSize: "13px", color: "#1d3557"}}));

  var layers = Map.layers();
  var anyActive = false;

  for (var i = 0; i < layers.length(); i++) {
    var layer = layers.get(i);
    if (!layer.getShown()) continue;
    anyActive = true;
    var name = layer.getName();

    if (name.indexOf("Comunas") !== -1) {
      legendContainer.add(ui.Label({value: "🏛️ Comunas en Botón Rojo:", style: {fontWeight: "bold", color: "#1d3557", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Límites comunales oficiales de Chile (346 comunas).", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Botón Rojo Calibrado") !== -1) {
      legendContainer.add(ui.Label({value: "🔴 Botón Rojo Calibrado (M1):", style: {fontWeight: "bold", color: "#d90429", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Rojo. Probabilidad ignición ≥ 60%, sequedad extrema de combustible.", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("NASA FIRMS") !== -1) {
      legendContainer.add(ui.Label({value: "🛰️ Anomalías Térmicas Satelitales (NASA FIRMS):", style: {fontWeight: "bold", color: "#ff0055", fontSize: "11px"}}));
      legendContainer.add(ui.Label({value: "Detecciones de calor en tiempo real por satélites VIIRS/MODIS.", style: {fontSize: "10px", color: "#555"}}));
    } else if (name.indexOf("Megaincendio") !== -1 || name.indexOf("Gran Incendio") !== -1) {
      legendContainer.add(ui.Label({value: "🟣 Grandes y Megaincendios (CONAF):", style: {fontWeight: "bold", color: "#7209b7", fontSize: "11px"}}));
    } else if (name.indexOf("Mapa de Calor") !== -1) {
      legendContainer.add(ui.Label({value: "💥 Mapa de Calor Incendios (KDE):", style: {fontWeight: "bold", color: "#bb3e03", fontSize: "11px"}}));
    }
  }

  if (!anyActive) {
    legendContainer.add(ui.Label({value: "No hay capas activas. Activa una capa en el menú Layers de la derecha.", style: {fontSize: "10px", color: "#888"}}));
  }
}

// 6. Inspector de Clic Interactivo
Map.onClick(function(coords) {
  var pt = ee.Geometry.Point([coords.lon, coords.lat]);
  var sampleComuna = coleccionComunas.filterBounds(pt).first();
  var sampleFires = coleccionIncendios.filterBounds(pt.buffer(8000)).limit(1);

  var merged = ee.Dictionary({
    "comuna": sampleComuna,
    "fuego": sampleFires
  });

  merged.evaluate(function(res) {
    inspectorPanel.clear();
    inspectorPanel.add(ui.Label({value: "📍 Inspector de Territorio", style: {fontWeight: "bold", fontSize: "12px"}}));
    inspectorPanel.add(ui.Label({value: "Coordenadas: " + coords.lat.toFixed(4) + ", " + coords.lon.toFixed(4), style: {fontSize: "11px"}}));

    if (res && res.comuna && res.comuna.properties) {
      var cProps = res.comuna.properties;
      inspectorPanel.add(ui.Label({value: "🏛️ Comuna: " + (cProps.comuna || cProps.Comuna || "Chile") + " (" + (cProps.region || cProps.Region || "") + ")", style: {fontWeight: "bold", fontSize: "11px", color: "#1d3557"}}));
    }

    if (res && res.fuego && res.fuego.features && res.fuego.features.length > 0) {
      var fProps = res.fuego.features[0].properties;
      inspectorPanel.add(ui.Label({value: "🔥 INCENDIO CERCANO (CONAF):", style: {fontWeight: "bold", color: "#d90429", fontSize: "12px"}}));
      inspectorPanel.add(ui.Label({value: "Comuna: " + fProps.comuna + " | Superficie: " + Number(fProps.area_ha).toFixed(1) + " ha", style: {fontSize: "11px"}}));
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

panel.add(ui.Label({value: "1. Monitoreo actual y eventos históricos:", style: {fontWeight: "bold", margin: "4px 0px 2px 0px"}}));

var dateSelect = ui.Select({
  items: [
    {label: "🌐 Pronóstico Hoy (Tiempo Real / GFS + FIRMS)", value: "HOY"},
    {label: "🔴 2023-02-03 (Megaincendios Biobío/Ñuble/Araucanía)", value: "2023-02-03"},
    {label: "🔴 2024-02-02 (Megaincendio Viña del Mar/Quilpué)", value: "2024-02-02"},
    {label: "🔴 2017-01-20 (Tormenta Las Máquinas - 211.000 ha)", value: "2017-01-20"},
    {label: "🟠 2023-01-15 (Día Típico de Verano - Focos Dispersos)", value: "2023-01-15"},
    {label: "🟠 2020-02-09 (Ola de Calor Focalizada La Araucanía)", value: "2020-02-09"},
    {label: "🟡 2023-11-15 (Primavera Central - Alerta Preventiva)", value: "2023-11-15"},
    {label: "🟢 2023-07-15 (Invierno Austral - 0 Alertas / 100% Verde)", value: "2023-07-15"}
  ],
  placeholder: "Seleccionar evento...",
  value: "HOY",
  onChange: function(val) {
    dateTextBox.setValue(val);
    cargarFecha(val);
  },
  style: {width: "95%"}
});
panel.add(dateSelect);

panel.add(ui.Label({value: "2. O escribe cualquier Fecha (2014-2024):", style: {margin: "8px 0px 2px 0px", fontWeight: "bold"}}));

var dateTextBox = ui.Textbox({placeholder: "AAAA-MM-DD", value: "HOY", style: {width: "60%"}});
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

// Carga Inicial: Pronóstico Hoy
cargarFecha("HOY");
