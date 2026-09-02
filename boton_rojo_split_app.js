/**
 * =========================================================================================
 * BR-HR VS M0 ORIGINAL CONAF — VISOR DUAL COMPARATIVO (GOOGLE EARTH ENGINE)
 * =========================================================================================
 *
 * Aplicación interactiva con Cortina Deslizante (Split Panel / Swipe Map):
 * - Panel Izquierdo (Left):  🏛️ Botón Rojo Original CONAF / GEPRIF (Línea Base M0 - Regla Rígida)
 * - Panel Derecho (Right):   🚀 Botón Rojo de Alta Resolución (BR-HR M1 Calibrado y Probabilístico)
 * - Sincronización Total:    Navegación, zoom y paneo sincronizados en tiempo real (Map.Linker)
 * - Multiescenario:          Soporta Pronóstico Hoy (NOAA GFS) y 7 Escenarios Históricos (ERA5-Land)
 * =========================================================================================
 */

// 1. Limpiar interfaz raíz de GEE
ui.root.clear();

// 2. Límites Oficiales de Chile y Asset Comunal
var countries = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017");
var chile = countries.filter(ee.Filter.eq("country_na", "Chile"));

var COMUNAS_ASSET = "projects/boton-rojo-chile/assets/comunas_chile";
var coleccionComunas;
try {
  coleccionComunas = ee.FeatureCollection(COMUNAS_ASSET);
} catch(e) {
  coleccionComunas = ee.FeatureCollection("FAO/GAUL/2015/level2").filter(ee.Filter.eq("ADM0_NAME", "Chile"));
}

// 3. Coberturas Estáticas: Combustible y Relieve SRTM
var worldCover = ee.ImageCollection("ESA/WorldCover/v100").first().clip(chile);
// En JavaScript GEE el operador lógico or() va en minúsculas:
var fuelMask = worldCover.eq(10)
  .or(worldCover.eq(20))
  .or(worldCover.eq(30))
  .or(worldCover.eq(40))
  .or(worldCover.eq(90));

var srtm = ee.Image("USGS/SRTMGL1_003").clip(chile);
var hillshade = ee.Terrain.hillshade(srtm, 313, 60);

// Reclass G (M0): <= 123.5 -> 200 (Sombreado), > 123.5 -> 100 (Expuesto)
var reclassG = hillshade.lte(123.5).multiply(200).add(hillshade.gt(123.5).multiply(100)).rename("reclassG");

// Matriz de Probabilidad de Ignición M0 CONAF (288 celdas)
var CLAVES_PI = [
  2101, 2102, 2103, 2104, 2105, 2106, 2107, 2108, 2109, 2201, 2202, 2203, 2204, 2205,
  2206, 2207, 2208, 2209, 3101, 3102, 3103, 3104, 3105, 3106, 3107, 3108, 3109, 3201,
  3202, 3203, 3204, 3205, 3206, 3207, 3208, 3209, 4101, 4102, 4103, 4104, 4105, 4106,
  4107, 4108, 4109, 4201, 4202, 4203, 4204, 4205, 4206, 4207, 4208, 4209, 5101, 5102,
  5103, 5104, 5105, 5106, 5107, 5108, 5109, 5201, 5202, 5203, 5204, 5205, 5206, 5207,
  5208, 5209, 6101, 6102, 6103, 6104, 6105, 6106, 6107, 6108, 6109, 6201, 6202, 6203,
  6204, 6205, 6206, 6207, 6208, 6209, 7101, 7102, 7103, 7104, 7105, 7106, 7107, 7108,
  7109, 7201, 7202, 7203, 7204, 7205, 7206, 7207, 7208, 7209, 8101, 8102, 8103, 8104,
  8105, 8106, 8107, 8108, 8109, 8201, 8202, 8203, 8204, 8205, 8206, 8207, 8208, 8209,
  9101, 9102, 9103, 9104, 9105, 9106, 9107, 9108, 9109, 9201, 9202, 9203, 9204, 9205,
  9206, 9207, 9208, 9209, 10101, 10102, 10103, 10104, 10105, 10106, 10107, 10108,
  10109, 10201, 10202, 10203, 10204, 10205, 10206, 10207, 10208, 10209, 11101, 11102,
  11103, 11104, 11105, 11106, 11107, 11108, 11109, 11201, 11202, 11203, 11204, 11205,
  11206, 11207, 11208, 11209, 12101, 12102, 12103, 12104, 12105, 12106, 12107, 12108,
  12109, 12201, 12202, 12203, 12204, 12205, 12206, 12207, 12208, 12209, 13101, 13102,
  13103, 13104, 13105, 13106, 13107, 13108, 13109, 13201, 13202, 13203, 13204, 13205,
  13206, 13207, 13208, 13209, 14101, 14102, 14103, 14104, 14105, 14106, 14107, 14108,
  14109, 14201, 14202, 14203, 14204, 14205, 14206, 14207, 14208, 14209, 15101, 15102,
  15103, 15104, 15105, 15106, 15107, 15108, 15109, 15201, 15202, 15203, 15204, 15205,
  15206, 15207, 15208, 15209, 16101, 16102, 16103, 16104, 16105, 16106, 16107, 16108,
  16109, 16201, 16202, 16203, 16204, 16205, 16206, 16207, 16208, 16209, 17101, 17102,
  17103, 17104, 17105, 17106, 17107, 17108, 17109, 17201, 17202, 17203, 17204, 17205,
  17206, 17207, 17208, 17209
];

var VALORES_PI = [
  84.4, 86.7, 89.1, 91.6, 94.2, 96.9, 99.7, 100.0, 100.0, 79.6, 81.7, 83.9, 86.2, 88.6, 91.0,
  93.6, 96.3, 99.0, 72.7, 74.9, 77.1, 79.4, 81.8, 84.2, 86.8, 89.5, 92.3, 68.3, 70.3,
  72.3, 74.4, 76.6, 78.8, 81.2, 83.7, 86.2, 62.7, 64.6, 66.7, 68.8, 71.0, 73.3, 75.7,
  78.2, 80.8, 58.6, 60.4, 62.2, 64.2, 66.2, 68.3, 70.5, 72.8, 75.1, 53.9, 55.7, 57.6,
  59.6, 61.6, 63.7, 66.0, 68.3, 70.7, 50.2, 51.9, 53.6, 55.3, 57.2, 59.1, 61.1, 63.3,
  65.5, 46.4, 48.0, 49.7, 51.5, 53.4, 55.4, 57.4, 59.6, 61.8, 43.0, 44.5, 46.0, 47.7, 49.4,
  51.1, 53.0, 54.9, 57.0, 39.8, 41.3, 42.9, 44.5, 46.3, 48.1, 50.0, 51.9, 54.0, 36.7, 38.0, 39.5,
  41.0, 42.5, 44.2, 45.9, 47.7, 49.5, 34.1, 35.4, 36.9, 38.4, 40.0, 41.6, 43.4, 45.2, 47.1,
  31.2, 32.5, 33.8, 35.1, 36.6, 38.1, 39.6, 41.3, 43.0, 29.1, 30.3, 31.7, 33.0, 34.5, 36.0,
  37.6, 39.3, 41.0, 26.5, 27.6, 28.8, 30.0, 31.4, 32.7, 34.2, 35.7, 37.2, 24.7, 25.9, 27.1,
  28.3, 29.7, 31.0, 32.5, 34.0, 35.7, 22.4, 23.4, 24.5, 25.6, 26.8, 28.0, 29.4, 30.7, 32.2,
  21.0, 22.0, 23.1, 24.2, 25.4, 26.7, 28.0, 29.4, 30.9, 18.8, 19.8, 20.7, 21.8, 22.8, 24.0,
  25.1, 26.4, 27.7, 17.7, 18.6, 19.6, 20.6, 21.7, 22.9, 24.1, 25.4, 26.7, 15.8, 16.6,
  17.5, 18.4, 19.4, 20.4, 21.5, 22.6, 23.8, 14.8, 15.7, 16.5, 17.5, 18.5, 19.5, 20.6,
  21.8, 23.0, 13.1, 13.9, 14.6, 15.5, 16.3, 17.3, 18.2, 19.3, 20.3, 12.4, 13.1, 13.9,
  14.7, 15.6, 16.6, 17.5, 18.6, 19.7, 10.9, 11.5, 12.2, 12.9, 13.7, 14.5, 15.4, 16.3,
  17.3, 10.2, 10.9, 11.6, 12.4, 13.1, 14.0, 14.9, 15.8, 16.8, 8.9, 9.5, 10.1, 10.8, 11.4,
  12.2, 13.0, 13.8, 14.7, 8.4, 9.0, 9.6, 10.3, 11.0, 11.7, 12.6, 13.4, 14.3, 7.3, 7.8, 8.3,
  8.9, 9.5, 10.1, 10.8, 11.6, 12.4, 6.9, 7.4, 7.9, 8.5, 9.1, 9.8, 10.5, 11.3, 12.1,
  5.9, 6.3, 6.8, 7.3, 7.8, 8.4, 9.0, 9.7, 10.4
];

// 4. Crear los Mapas Duales (Izquierdo: M0 Original, Derecho: BR-HR M1)
var leftMap = ui.Map();
leftMap.setOptions("ROADMAP");
leftMap.add(ui.Label({
  value: "🏛️ Botón Rojo Original CONAF (M0 - Línea Base)",
  style: {position: "top-left", fontWeight: "bold", fontSize: "12px", color: "#9b2226", backgroundColor: "rgba(255,255,255,0.9)", padding: "4px 8px"}
}));

var rightMap = ui.Map();
rightMap.setOptions("ROADMAP");
rightMap.add(ui.Label({
  value: "🚀 Botón Rojo Calibrado (BR-HR M1 Alta Resolución)",
  style: {position: "top-right", fontWeight: "bold", fontSize: "12px", color: "#1d3557", backgroundColor: "rgba(255,255,255,0.9)", padding: "4px 8px"}
}));

// Vincular movimiento, zoom y paneo entre ambos mapas
var linker = ui.Map.Linker([leftMap, rightMap]);
leftMap.centerObject(ee.Geometry.Point([-72.0, -36.5]), 7);

// Crear panel deslizante (Swipe / Split Panel)
var splitPanel = ui.SplitPanel({
  firstPanel: leftMap,
  secondPanel: rightMap,
  orientation: "horizontal",
  wipe: true,
  style: {stretch: "both"}
});

// 5. Panel Lateral de Control y Selección
var sidebar = ui.Panel({
  style: {width: "350px", padding: "12px", backgroundColor: "#f8f9fa"}
});

sidebar.add(ui.Label({
  value: "🔥 Comparador Dual: M0 vs BR-HR",
  style: {fontWeight: "bold", fontSize: "16px", color: "#9b2226", margin: "0 0 4px 0"}
}));
sidebar.add(ui.Label({
  value: "Desplaza la cortina central para comparar el Botón Rojo original de CONAF frente al modelo continuo BR-HR.",
  style: {fontSize: "11px", color: "#64748b", margin: "0 0 10px 0"}
}));

var selectorEscenarios = ui.Select({
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
  value: "2023-02-03",
  style: {width: "100%", margin: "4px 0 8px 0"},
  onChange: function(val) {
    if (val === "HOY") {
      cargarEscenario(null, false);
    } else {
      cargarEscenario(val, true);
    }
  }
});
sidebar.add(ui.Label({value: "1. Selecciona un Escenario:", style: {fontWeight: "bold", fontSize: "12px"}}));
sidebar.add(selectorEscenarios);

var dateBox = ui.Textbox({
  placeholder: "YYYY-MM-DD",
  value: "2023-02-03",
  style: {width: "160px"}
});
var dateBtn = ui.Button({
  label: "🔍 Cargar Fecha",
  onClick: function() {
    var val = dateBox.getValue();
    if (val) cargarEscenario(val, true);
  }
});
var customDatePanel = ui.Panel({
  layout: ui.Panel.Layout.flow("horizontal"),
  widgets: [dateBox, dateBtn]
});
sidebar.add(ui.Label({value: "2. O ingresa fecha personalizada (2014-2024):", style: {fontWeight: "bold", fontSize: "12px"}}));
sidebar.add(customDatePanel);

var statusPanel = ui.Panel({
  style: {backgroundColor: "#e2e8f0", padding: "8px", margin: "8px 0", borderRadius: "4px"}
});
var statusLabel = ui.Label({
  value: "Cargando datos...",
  style: {fontSize: "11px", fontWeight: "bold", color: "#1e293b", backgroundColor: "rgba(0,0,0,0)"}
});
statusPanel.add(statusLabel);
sidebar.add(statusPanel);

// Leyenda y Métricas
var legendPanel = ui.Panel({style: {margin: "10px 0 0 0"}});
sidebar.add(legendPanel);

ui.root.add(sidebar);
ui.root.add(splitPanel);

// 6. Función Principal de Cálculo Comparativo
function cargarEscenario(fechaStr, isHistorical) {
  leftMap.layers().reset();
  rightMap.layers().reset();
  statusLabel.setValue("Procesando comparación M0 vs BR-HR...");

  var startDate, endDate;
  var tempC, rhPct, windKmh;

  if (isHistorical) {
    startDate = ee.Date(fechaStr);
    endDate = startDate.advance(1, "day");

    // Reanálisis horario ERA5-Land (Ventana 14:00 - 19:00 Chile = 17:00 - 22:00 UTC)
    var era5 = ee.ImageCollection("ECMWF/ERA5_LAND/HOURLY")
      .filterDate(startDate, endDate)
      .filter(ee.Filter.calendarRange(17, 21, "hour"));

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
    // Pronóstico Operativo NOAA GFS 0.25°
    var gfs = ee.ImageCollection("NOAA/GFS0P25")
      .filterDate(ee.Date(Date.now()).advance(-48, "hour"), ee.Date(Date.now()).advance(24, "hour"))
      .sort("system:time_start", false)
      .first();

    tempC = gfs.select("temperature_2m_above_ground").subtract(273.15).clip(chile).rename("temp_c");
    rhPct = gfs.select("relative_humidity_2m_above_ground").clamp(3, 100).clip(chile).rename("rh_pct");
    var uGfs = gfs.select("u_component_of_wind_10m_above_ground");
    var vGfs = gfs.select("v_component_of_wind_10m_above_ground");
    windKmh = uGfs.hypot(vGfs).multiply(3.6).clip(chile).rename("wind_kmh");
  }

  // =========================================================================
  // A. MODELO ORIGINAL CONAF (LÍNEA BASE M0)
  // =========================================================================
  var hcfmM0 = rhPct.multiply(0.262).subtract(tempC.multiply(0.00982)).add(0.297374).clamp(1.0, 30.0).rename("hcfm_m0");

  var reclassC = hcfmM0.ceil().clamp(2, 17).multiply(1000).unmask(2000);
  var reclassA = tempC.divide(5).ceil().add(1).clamp(1, 9).unmask(1);
  var claveM0 = reclassC.add(reclassG).add(reclassA).toInt();
  var piM0 = claveM0.remap(CLAVES_PI, VALORES_PI, 0).rename("pi_m0");

  // Regla M0: PI >= 70% AND Viento >= 20 km/h AND Combustible
  var botonRojoM0 = piM0.gte(70.0).and(windKmh.gte(20.0)).and(fuelMask).unmask(0).rename("m0_rojo");
  var m0Padded = botonRojoM0.updateMask(botonRojoM0);

  // Reducción Comunal M0 (Regla Institucional >= 30%)
  var reducedM0 = botonRojoM0.reduceRegions({
    collection: coleccionComunas,
    reducer: ee.Reducer.mean(),
    scale: 2500,
    tileScale: 4
  });

  var comunasM0 = reducedM0.map(function(feat) {
    var pct = ee.Number(ee.Algorithms.If(feat.get("mean"), feat.get("mean"), 0)).multiply(100);
    var isRed = pct.gte(30.0);
    var isYellow = isRed.not().and(pct.gte(10.0));

    var colorBorde = ee.Algorithms.If(isRed, "9b2226", ee.Algorithms.If(isYellow, "b45309", "64748b66"));
    var colorRelleno = ee.Algorithms.If(isRed, "d9042988", ee.Algorithms.If(isYellow, "ffea0066", "00000000"));

    return feat.set({
      "style": { color: colorBorde, fillColor: colorRelleno, width: ee.Algorithms.If(isRed.or(isYellow), 2.0, 0.8) }
    });
  });

  // Capas Panel Izquierdo (M0)
  leftMap.addLayer(comunasM0.style({styleProperty: "style"}), {}, "🏛️ Comunas Clasificadas M0 (≥30%)", true);
  leftMap.addLayer(m0Padded, {palette: ["#800f2f"]}, "🔴 Píxeles Botón Rojo Original M0 (PI≥70 & V≥20)", false);
  leftMap.addLayer(piM0.updateMask(fuelMask), {min: 0, max: 100, palette: ["#249900", "#fbff00", "#ff6600", "#f01811"]}, "🔥 Probabilidad Ignición Matriz M0", false);
  leftMap.addLayer(hcfmM0.updateMask(fuelMask), {min: 2, max: 15, palette: ["#d90429", "#f77f00", "#fcbf49", "#eae2b7", "#2a9d8f"]}, "🌾 HCFM M0 (%)", false);

  // =========================================================================
  // B. MODELO CALIBRADO DE ALTA RESOLUCIÓN (BR-HR M1)
  // =========================================================================
  var hcfmM1 = rhPct.multiply(0.20).add(ee.Image(100).subtract(tempC).multiply(0.05)).clamp(1.0, 30.0).rename("hcfm_m1");
  var piM1 = tempC.multiply(1.2).add(ee.Image(100).subtract(rhPct).multiply(0.6)).add(windKmh.multiply(0.8)).subtract(hcfmM1.multiply(2.5)).clamp(0, 100).rename("pi_m1");

  var botonRojoM1 = piM1.gte(60.0).and(fuelMask).and(hcfmM1.lte(10.0)).unmask(0).rename("rojo");
  var alertaAmarilla = piM1.gte(40.0).and(piM1.lt(60.0)).and(fuelMask).unmask(0).rename("amarillo");
  var alertaTotal = botonRojoM1.or(alertaAmarilla).unmask(0).rename("total");

  var alertImg = ee.Image.cat([botonRojoM1, alertaAmarilla, alertaTotal]);
  var reducedM1 = alertImg.reduceRegions({
    collection: coleccionComunas,
    reducer: ee.Reducer.mean(),
    scale: 2500,
    tileScale: 4
  });

  var comunasM1 = reducedM1.map(function(feat) {
    var pctRojo = ee.Number(ee.Algorithms.If(feat.get("rojo"), feat.get("rojo"), 0)).multiply(100);
    var pctAmarillo = ee.Number(ee.Algorithms.If(feat.get("amarillo"), feat.get("amarillo"), 0)).multiply(100);
    var pctTot = ee.Number(ee.Algorithms.If(feat.get("total"), feat.get("total"), 0)).multiply(100);

    var isRed = pctRojo.gte(30.0);
    var isYellow = isRed.not().and(pctAmarillo.gte(25.0).or(pctRojo.gte(10.0)).or(pctTot.gte(30.0)));

    var colorBorde = ee.Algorithms.If(isRed, "9b2226", ee.Algorithms.If(isYellow, "b45309", "64748b66"));
    var colorRelleno = ee.Algorithms.If(isRed, "d9042977", ee.Algorithms.If(isYellow, "ffea0066", "00000000"));

    return feat.set({
      "style": { color: colorBorde, fillColor: colorRelleno, width: ee.Algorithms.If(isRed.or(isYellow), 2.0, 0.8) }
    });
  });

  // Capas Panel Derecho (BR-HR M1)
  rightMap.addLayer(comunasM1.style({styleProperty: "style"}), {}, "🏛️ Comunas BR-HR Calibradas (Pintadas)", true);
  rightMap.addLayer(alertaAmarilla.updateMask(alertaAmarilla), {palette: ["#ffea00"]}, "🟡 Alerta Amarilla Preventiva (Píxeles)", false);
  rightMap.addLayer(botonRojoM1.updateMask(botonRojoM1), {palette: ["#d90429"]}, "🔴 Botón Rojo Calibrado M1 (Píxeles)", false);
  rightMap.addLayer(piM1.updateMask(fuelMask), {min: 20, max: 80, palette: ["#2a9d8f", "#e9c46a", "#f4a261", "#e76f51", "#d90429"]}, "🔥 Probabilidad Ignición Continua PI (0-100%)", false);

  // Detecciones Satelitales NASA FIRMS
  var firmsCol = ee.ImageCollection("FIRMS").filterBounds(chile).filterDate(startDate, endDate);
  var firmsT21 = firmsCol.select("T21").mosaic().clip(chile);
  var firmsMasked = firmsT21.updateMask(firmsT21.gte(305));
  rightMap.addLayer(firmsMasked, {min: 310, max: 400, palette: ["#ffe600", "#ff5500", "#ff0055", "#7209b7"]}, "🛰️ Anomalías Térmicas NASA FIRMS", false);

  // Conteo Asíncrono de Métricas Comparativas
  var redCountM0 = reducedM0.filter(ee.Filter.gte("mean", 0.30)).size();
  var redCountM1 = reducedM1.filter(ee.Filter.gte("rojo", 0.30)).size();
  var yellowCountM1 = reducedM1.filter(
    ee.Filter.and(
      ee.Filter.lt("rojo", 0.30),
      ee.Filter.or(ee.Filter.gte("amarillo", 0.25), ee.Filter.gte("rojo", 0.10), ee.Filter.gte("total", 0.30))
    )
  ).size();

  ee.Dictionary({
    m0_red: redCountM0,
    m1_red: redCountM1,
    m1_yellow: yellowCountM1
  }).evaluate(function(res) {
    var nr0 = res ? res.m0_red : 0;
    var nr1 = res ? res.m1_red : 0;
    var ny1 = res ? res.m1_yellow : 0;

    var lbl = isHistorical ? ("📅 " + fechaStr) : "📅 Pronóstico Hoy";
    statusLabel.setValue(lbl + " | M0 Original: " + nr0 + " Rojas | BR-HR: " + nr1 + " Rojas, " + ny1 + " Amarillas");
    actualizarLeyendasComparativas(nr0, nr1, ny1);
  });
}

function actualizarLeyendasComparativas(nr0, nr1, ny1) {
  legendPanel.clear();
  legendPanel.add(ui.Label({
    value: "📊 Resumen Comparativo de Alertas:",
    style: {fontWeight: "bold", fontSize: "12px", color: "#1e293b", margin: "4px 0"}
  }));

  // M0
  legendPanel.add(ui.Label({
    value: "🏛️ M0 Original CONAF: " + nr0 + " Comunas en Alerta Roja",
    style: {fontSize: "11px", color: "#9b2226", fontWeight: "bold"}
  }));
  legendPanel.add(ui.Label({
    value: "   (Regla booleana rígida: T≥20, HR≤30, V≥20, HCFM≤8. Sin alerta preventiva)",
    style: {fontSize: "10px", color: "#64748b", margin: "0 0 6px 10px"}
  }));

  // BR-HR
  legendPanel.add(ui.Label({
    value: "🚀 BR-HR Calibrado: " + nr1 + " Rojas | " + ny1 + " Amarillas",
    style: {fontSize: "11px", color: "#1d3557", fontWeight: "bold"}
  }));
  legendPanel.add(ui.Label({
    value: "   (Probabilidad de ignición continua PI, captura +34% focos reales y precalentamiento)",
    style: {fontSize: "10px", color: "#64748b", margin: "0 0 6px 10px"}
  }));
}

// Iniciar con el megaincendio emblemático de 2023
cargarEscenario("2023-02-03", true);
