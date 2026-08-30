/**
 * src/gee/baseline_module.js — Módulo Earth Engine para la réplica exacta y corregida
 * del baseline Botón Rojo de CONAF (M0 — BR-CONAF).
 *
 * Correcciones técnicas respecto al script legado:
 * 1. Resampling bilineal restringido estrictamente a capas meteorológicas continuas (T, HR, u, v).
 *    Las capas categóricas (Reclass A, C, G), matriz PI y banderas booleanas (BR) NO sufren
 *    interpolación bilineal, previniendo valores fraccionarios espurios.
 * 2. Manejo seguro de bordes térmicos (T > 40 °C clamped a clase 9 en vez de NoData).
 * 3. Modularización para consumo como librería o script independiente.
 */

var tables = {
  UMBRAL_PI: 70.0,
  UMBRAL_VIENTO: 20.0,
  HORA_INICIO: 14,
  HORA_FIN: 18,
  CLASES_COMBUSTIBLE: [10, 20, 30, 40, 90],
  HILLSHADE_AZIMUT: 313.0,
  HILLSHADE_ALTITUD: 60.0,
  ESCALA_INDICE: 2000,
  ESCALA_ZONAL: 500
};

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
  84.4, 86.7, 89.1, 91.6, 94.2, 96.9, 99.7, 100, 100, 79.6, 81.7, 83.9, 86.2, 88.6, 91,
  93.6, 96.3, 99, 72.7, 74.9, 77.1, 79.4, 81.8, 84.2, 86.8, 89.5, 92.3, 68.3, 70.3,
  72.3, 74.4, 76.6, 78.8, 81.2, 83.7, 86.2, 62.7, 64.6, 66.7, 68.8, 71, 73.3, 75.7,
  78.2, 80.8, 58.6, 60.4, 62.2, 64.2, 66.2, 68.3, 70.5, 72.8, 75.1, 53.9, 55.7, 57.6,
  59.6, 61.6, 63.7, 66, 68.3, 70.7, 50.2, 51.9, 53.6, 55.3, 57.2, 59.1, 61.1, 63.3,
  65.5, 46.4, 48, 49.7, 51.5, 53.4, 55.4, 57.4, 59.6, 61.8, 43, 44.5, 46, 47.7, 49.4,
  51.1, 53, 54.9, 57, 39.8, 41.3, 42.9, 44.5, 46.3, 48.1, 50, 51.9, 54, 36.7, 38, 39.5,
  41, 42.5, 44.2, 45.9, 47.7, 49.5, 34.1, 35.4, 36.9, 38.4, 40, 41.6, 43.4, 45.2, 47.1,
  31.2, 32.5, 33.8, 35.1, 36.6, 38.1, 39.6, 41.3, 43, 29.1, 30.3, 31.7, 33, 34.5, 36,
  37.6, 39.3, 41, 26.5, 27.6, 28.8, 30, 31.4, 32.7, 34.2, 35.7, 37.2, 24.7, 25.9, 27.1,
  28.3, 29.7, 31, 32.5, 34, 35.7, 22.4, 23.4, 24.5, 25.6, 26.8, 28, 29.4, 30.7, 32.2,
  21, 22, 23.1, 24.2, 25.4, 26.7, 28, 29.4, 30.9, 18.8, 19.8, 20.7, 21.8, 22.8, 24,
  25.1, 26.4, 27.7, 17.7, 18.6, 19.6, 20.6, 21.7, 22.9, 24.1, 25.4, 26.7, 15.8, 16.6,
  17.5, 18.4, 19.4, 20.4, 21.5, 22.6, 23.8, 14.8, 15.7, 16.5, 17.5, 18.5, 19.5, 20.6,
  21.8, 23, 13.1, 13.9, 14.6, 15.5, 16.3, 17.3, 18.2, 19.3, 20.3, 12.4, 13.1, 13.9,
  14.7, 15.6, 16.6, 17.5, 18.6, 19.7, 10.9, 11.5, 12.2, 12.9, 13.7, 14.5, 15.4, 16.3,
  17.3, 10.2, 10.9, 11.6, 12.4, 13.1, 14, 14.9, 15.8, 16.8, 8.9, 9.5, 10.1, 10.8, 11.4,
  12.2, 13, 13.8, 14.7, 8.4, 9, 9.6, 10.3, 11, 11.7, 12.6, 13.4, 14.3, 7.3, 7.8, 8.3,
  8.9, 9.5, 10.1, 10.8, 11.6, 12.4, 6.9, 7.4, 7.9, 8.5, 9.1, 9.8, 10.5, 11.3, 12.1,
  5.9, 6.3, 6.8, 7.3, 7.8, 8.4, 9, 9.7, 10.4
];

/**
 * Obtiene la máscara de superficie combustible estática (ESA WorldCover 2021).
 */
function getCombustibleMask() {
  var wc = ee.ImageCollection('ESA/WorldCover/v200').first();
  return wc.remap([10, 20, 30, 40, 90], [1, 1, 1, 1, 1], 0).rename('combustible');
}

/**
 * Obtiene la capa de sombreado Reclass G (SRTM 90m, az=313°, alt=60°).
 */
function getReclassG() {
  var dem = ee.Image('CGIAR/SRTM90_V4');
  var hs = ee.Terrain.hillshade(dem, tables.HILLSHADE_AZIMUT, tables.HILLSHADE_ALTITUD);
  return hs.lte(123.5).multiply(200).add(hs.gt(123.5).multiply(100)).rename('reclassG');
}

/**
 * Evalúa un paso horario del Botón Rojo M0 sobre una imagen continua.
 */
function computeHourlyBR(gfsImg, reclassGImg) {
  // 1. Resamplear únicamente los campos meteorológicos continuos
  var gfsResampled = gfsImg.resample('bilinear');
  var t = gfsResampled.select('temperature_2m_above_ground');
  var hr = gfsResampled.select('relative_humidity_2m_above_ground').clamp(1.0, 100.0);
  var u = gfsResampled.select('u_component_of_wind_10m_above_ground');
  var v = gfsResampled.select('v_component_of_wind_10m_above_ground');

  // 2. Variables derivadas
  var viento = u.hypot(v).multiply(3.6).rename('VV');
  var hcfm = hr.multiply(0.262).subtract(t.multiply(0.00982)).add(0.297374).rename('HC');

  // 3. Reclasificaciones discretas (sin resampling posterior)
  var reclassC = hcfm.ceil().clamp(2, 17).multiply(1000);
  var reclassA = t.divide(5).ceil().add(1).clamp(1, 9);
  var clave = reclassC.add(reclassGImg).add(reclassA).rename('clave');

  // 4. Matriz PI y regla de activación Botón Rojo
  var pi = clave.remap(CLAVES_PI, VALORES_PI).rename('PI');
  var br = pi.gte(tables.UMBRAL_PI).and(viento.gte(tables.UMBRAL_VIENTO)).rename('BR');

  return ee.Image.cat([
    t.rename('TP'),
    hr.rename('HR'),
    hcfm,
    viento,
    pi,
    br
  ]).set({
    'system:time_start': gfsImg.get('forecast_time'),
    fecha_local: gfsImg.get('fecha_local'),
    hora_local: gfsImg.get('hora_local')
  });
}

// Exportación para módulos GEE
exports = {
  tables: tables,
  CLAVES_PI: CLAVES_PI,
  VALORES_PI: VALORES_PI,
  getCombustibleMask: getCombustibleMask,
  getReclassG: getReclassG,
  computeHourlyBR: computeHourlyBR
};
