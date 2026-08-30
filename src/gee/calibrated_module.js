/**
 * src/gee/calibrated_module.js — Módulo de Inferencia Operacional BR-HR en Google Earth Engine.
 *
 * Implementa el cálculo píxel a píxel del Botón Rojo Original (M0) y Recalibrado (M1 - BR-CAL),
 * junto con la agregación zonal sobre hexágonos H3 resolución 8.
 */

var MATRIZ_CALIBRADA = (function() {
  // 288 claves compuestas y valores empíricos calibrados con histórico de Chile (2014-2021)
  return {
    "from": [
      2101, 2102, 2103, 2104, 2105, 2106, 2107, 2108, 2109,
      2201, 2202, 2203, 2204, 2205, 2206, 2207, 2208, 2209,
      3101, 3102, 3103, 3104, 3105, 3106, 3107, 3108, 3109,
      3201, 3202, 3203, 3204, 3205, 3206, 3207, 3208, 3209,
      4101, 4102, 4103, 4104, 4105, 4106, 4107, 4108, 4109,
      4201, 4202, 4203, 4204, 4205, 4206, 4207, 4208, 4209,
      5101, 5102, 5103, 5104, 5105, 5106, 5107, 5108, 5109,
      5201, 5202, 5203, 5204, 5205, 5206, 5207, 5208, 5209,
      6101, 6102, 6103, 6104, 6105, 6106, 6107, 6108, 6109,
      6201, 6202, 6203, 6204, 6205, 6206, 6207, 6208, 6209,
      7101, 7102, 7103, 7104, 7105, 7106, 7107, 7108, 7109,
      7201, 7202, 7203, 7204, 7205, 7206, 7207, 7208, 7209,
      8101, 8102, 8103, 8104, 8105, 8106, 8107, 8108, 8109,
      8201, 8202, 8203, 8204, 8205, 8206, 8207, 8208, 8209,
      9101, 9102, 9103, 9104, 9105, 9106, 9107, 9108, 9109,
      9201, 9202, 9203, 9204, 9205, 9206, 9207, 9208, 9209,
      10101, 10102, 10103, 10104, 10105, 10106, 10107, 10108, 10109,
      10201, 10202, 10203, 10204, 10205, 10206, 10207, 10208, 10209,
      11101, 11102, 11103, 11104, 11105, 11106, 11107, 11108, 11109,
      11201, 11202, 11203, 11204, 11205, 11206, 11207, 11208, 11209,
      12101, 12102, 12103, 12104, 12105, 12106, 12107, 12108, 12109,
      12201, 12202, 12203, 12204, 12205, 12206, 12207, 12208, 12209,
      13101, 13102, 13103, 13104, 13105, 13106, 13107, 13108, 13109,
      13201, 13202, 13203, 13204, 13205, 13206, 13207, 13208, 13209,
      14101, 14102, 14103, 14104, 14105, 14106, 14107, 14108, 14109,
      14201, 14202, 14203, 14204, 14205, 14206, 14207, 14208, 14209,
      15101, 15102, 15103, 15104, 15105, 15106, 15107, 15108, 15109,
      15201, 15202, 15203, 15204, 15205, 15206, 15207, 15208, 15209,
      16101, 16102, 16103, 16104, 16105, 16106, 16107, 16108, 16109,
      16201, 16202, 16203, 16204, 16205, 16206, 16207, 16208, 16209,
      17101, 17102, 17103, 17104, 17105, 17106, 17107, 17108, 17109,
      17201, 17202, 17203, 17204, 17205, 17206, 17207, 17208, 17209
    ],
    "to": [
      42.2, 43.4, 44.5, 45.8, 47.1, 48.3, 49.5, 50.8, 52.3,
      41.5, 42.1, 43.0, 44.2, 45.3, 46.5, 47.7, 48.9, 50.1,
      40.5, 41.2, 42.1, 43.2, 44.4, 45.7, 46.9, 48.2, 49.3,
      39.8, 40.5, 41.3, 42.4, 43.6, 44.8, 45.9, 47.0, 48.1,
      38.7, 39.4, 40.3, 41.4, 42.7, 44.0, 45.3, 46.7, 50.0,
      37.9, 38.6, 39.5, 40.6, 41.9, 43.1, 44.4, 45.6, 46.8,
      36.9, 37.6, 38.5, 39.7, 41.1, 42.4, 43.8, 49.5, 50.7,
      36.0, 36.7, 37.6, 38.8, 40.1, 41.4, 42.7, 44.1, 45.4,
      35.0, 35.7, 36.6, 37.9, 39.3, 40.7, 42.2, 43.7, 45.2,
      34.1, 34.8, 35.7, 36.9, 38.3, 39.7, 41.1, 42.5, 43.9,
      33.0, 33.7, 34.7, 36.0, 37.4, 39.0, 40.5, 42.1, 43.7,
      32.1, 32.8, 33.7, 35.0, 36.4, 37.9, 39.4, 40.9, 42.4,
      31.0, 31.7, 32.7, 34.0, 35.6, 37.2, 38.8, 40.5, 42.2,
      30.1, 30.8, 31.7, 33.0, 34.5, 36.1, 37.7, 39.3, 40.9,
      28.9, 29.6, 30.6, 32.0, 33.6, 35.3, 37.1, 38.9, 40.7,
      28.0, 28.7, 29.6, 31.0, 32.6, 34.2, 35.9, 37.6, 39.3,
      26.7, 27.4, 28.5, 29.9, 31.6, 33.4, 35.3, 37.2, 39.1,
      25.8, 26.5, 27.5, 28.9, 30.5, 32.3, 34.1, 35.9, 37.7,
      24.4, 25.2, 26.2, 27.7, 29.5, 31.4, 33.4, 35.4, 37.5,
      23.5, 24.2, 25.2, 26.7, 28.4, 30.3, 32.2, 34.1, 36.0,
      22.0, 22.8, 23.9, 25.4, 27.2, 29.2, 31.3, 33.5, 35.7,
      21.1, 21.8, 22.9, 24.3, 26.1, 28.1, 30.1, 32.1, 34.1,
      19.4, 20.2, 21.4, 22.9, 24.8, 26.9, 29.1, 31.4, 33.8,
      18.5, 19.2, 20.3, 21.8, 23.7, 25.7, 27.8, 29.9, 32.1,
      16.6, 17.4, 18.6, 20.2, 22.2, 24.4, 26.8, 29.2, 31.7,
      15.7, 16.4, 17.6, 19.1, 21.0, 23.2, 25.4, 27.7, 30.0,
      13.5, 14.3, 15.6, 17.3, 19.3, 21.7, 24.2, 26.8, 29.5,
      12.6, 13.4, 14.6, 16.2, 18.2, 20.4, 22.8, 25.2, 27.7,
      10.1, 10.9, 12.2, 13.9, 16.1, 18.6, 21.3, 24.1, 27.0,
      9.2, 10.0, 11.2, 12.9, 15.0, 17.3, 19.8, 22.4, 25.1,
      6.2, 7.0, 8.3, 10.2, 12.5, 15.2, 18.0, 21.1, 24.2,
      5.4, 6.1, 7.3, 9.1, 11.3, 13.8, 16.5, 19.3, 22.2
    ]
  };
})();

/**
 * Calcula el Hillshade de referencia SRTM 30m para Chile.
 */
function calcularHillshadeSRTM() {
  var srtm = ee.Image("USGS/SRTMGL1_003");
  var terrain = ee.Algorithms.Terrain(srtm);
  var slopeRad = terrain.select("slope").multiply(Math.PI / 180.0);
  var aspectRad = terrain.select("aspect").multiply(Math.PI / 180.0);

  var azimuthRad = 313.0 * (Math.PI / 180.0);
  var altitudeRad = 60.0 * (Math.PI / 180.0);

  var cosZenith = Math.sin(altitudeRad);
  var sinZenith = Math.cos(altitudeRad);

  var hs = slopeRad.cos().multiply(cosZenith)
    .add(slopeRad.sin().multiply(sinZenith).multiply(aspectRad.subtract(azimuthRad).cos()))
    .multiply(255.0);

  return hs.rename("hillshade");
}

/**
 * Reclasifica Hillshade (G): > 123.5 -> 100 (Expuesto), <= 123.5 -> 200 (Sombreado).
 */
function reclassG(hsImage) {
  return hsImage.gt(123.5).multiply(100).add(hsImage.lte(123.5).multiply(200)).rename("reclass_g");
}

/**
 * Reclasifica Temperatura (A): 9 clases (1 a 9).
 */
function reclassA(tempImage) {
  return tempImage.lt(10).multiply(1)
    .add(tempImage.gte(10).and(tempImage.lt(15)).multiply(2))
    .add(tempImage.gte(15).and(tempImage.lt(20)).multiply(3))
    .add(tempImage.gte(20).and(tempImage.lt(25)).multiply(4))
    .add(tempImage.gte(25).and(tempImage.lt(30)).multiply(5))
    .add(tempImage.gte(30).and(tempImage.lt(33)).multiply(6))
    .add(tempImage.gte(33).and(tempImage.lt(35)).multiply(7))
    .add(tempImage.gte(35).and(tempImage.lt(40)).multiply(8))
    .add(tempImage.gte(40).multiply(9))
    .rename("reclass_a");
}

/**
 * Reclasifica HCFM (C): 16 clases (2000 a 17000).
 */
function reclassC(hcfmImage) {
  return hcfmImage.lt(1.5).multiply(2000)
    .add(hcfmImage.gte(1.5).and(hcfmImage.lt(3.5)).multiply(3000))
    .add(hcfmImage.gte(3.5).and(hcfmImage.lt(5.5)).multiply(4000))
    .add(hcfmImage.gte(5.5).and(hcfmImage.lt(7.5)).multiply(5000))
    .add(hcfmImage.gte(7.5).and(hcfmImage.lt(9.5)).multiply(6000))
    .add(hcfmImage.gte(9.5).and(hcfmImage.lt(11.5)).multiply(7000))
    .add(hcfmImage.gte(11.5).and(hcfmImage.lt(13.5)).multiply(8000))
    .add(hcfmImage.gte(13.5).and(hcfmImage.lt(15.5)).multiply(9000))
    .add(hcfmImage.gte(15.5).and(hcfmImage.lt(17.5)).multiply(10000))
    .add(hcfmImage.gte(17.5).and(hcfmImage.lt(19.5)).multiply(11000))
    .add(hcfmImage.gte(19.5).and(hcfmImage.lt(21.5)).multiply(12000))
    .add(hcfmImage.gte(21.5).and(hcfmImage.lt(23.5)).multiply(13000))
    .add(hcfmImage.gte(23.5).and(hcfmImage.lt(25.5)).multiply(14000))
    .add(hcfmImage.gte(25.5).and(hcfmImage.lt(27.5)).multiply(15000))
    .add(hcfmImage.gte(27.5).and(hcfmImage.lt(29.5)).multiply(16000))
    .add(hcfmImage.gte(29.5).multiply(17000))
    .rename("reclass_c");
}

/**
 * Procesa un paso horario y genera las bandas de M0 y M1.
 */
function procesarPasoHorario(temp, rh, windKmh, hs) {
  // Resampling bilineal ÚNICAMENTE sobre bandas continuas
  var t_res = temp.resample("bilinear");
  var rh_res = rh.resample("bilinear");
  var w_res = windKmh.resample("bilinear");

  var hcfm = rh_res.multiply(0.262).subtract(t_res.multiply(0.00982)).add(0.297374).rename("hcfm");

  var rcA = reclassA(t_res);
  var rcC = reclassC(hcfm);
  var rcG = reclassG(hs);

  var clave = rcC.add(rcG).add(rcA).rename("clave");

  // Matriz Calibrada M1
  var piM1 = clave.remap(MATRIZ_CALIBRADA.from, MATRIZ_CALIBRADA.to, 50.0).rename("pi_m1");
  // Umbrales óptimos M1: PI >= 45 %, Viento >= 22 km/h
  var brM1 = piM1.gte(45.0).and(w_res.gte(22.0)).rename("br_m1");

  // Matriz Baseline M0: PI >= 70 %, Viento >= 20 km/h
  var brM0 = piM1.gte(70.0).and(w_res.gte(20.0)).rename("br_m0");

  return ee.Image.cat([t_res.rename("temp"), rh_res.rename("rh"), w_res.rename("wind"), hcfm, piM1, brM1, brM0]);
}

/**
 * Agrega el riesgo zonal sobre una FeatureCollection de hexágonos H3.
 */
function agregarRiesgoH3(imageRisk, h3Collection, scale) {
  scale = scale || 1000;
  return imageRisk.reduceRegions({
    collection: h3Collection,
    reducer: ee.Reducer.max().combine({
      reducer2: ee.Reducer.mean(),
      sharedInputs: true
    }),
    scale: scale,
    crs: "EPSG:4326"
  });
}

exports = {
  calcularHillshadeSRTM: calcularHillshadeSRTM,
  reclassA: reclassA,
  reclassC: reclassC,
  reclassG: reclassG,
  procesarPasoHorario: procesarPasoHorario,
  agregarRiesgoH3: agregarRiesgoH3,
  MATRIZ_CALIBRADA: MATRIZ_CALIBRADA
};
