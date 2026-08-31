/**
 * boton_rojo_gee.js — Replica del indice "Boton Rojo" de CONAF
 * en Google Earth Engine, el mismo entorno en que CONAF lo produce.
 *
 * Cadena de calculo (ver informe metodologico UIA para trazabilidad):
 *
 *   NOAA/GFS0P25 (ultima corrida)
 *     -> ventana 14:00-18:59 hora local, dias d0..d4
 *     -> HCFM = 0,297374 + 0,262*HR - 0,00982*T
 *     -> clave = ReclassC(HCFM) + ReclassG(hillshade SRTM) + ReclassA(T)
 *     -> PI = MATRIZ[clave]
 *     -> Boton Rojo = (PI >= 70) AND (viento >= 20 km/h)
 *     -> horas = numero de pasos horarios que cumplen la condicion (1..5)
 *     -> mascara ESA WorldCover v200 (2021), clases 10/20/30/40/90
 *     -> estadistica zonal por comuna: SUM_br_ha, com_ha, proportion
 *
 * ADVERTENCIA. La matriz de 288 celdas incluida al final es una RECONSTRUCCION
 * a partir de la ecuacion de probabilidad de ignicion de Rothermel/BehavePlus.
 * CONAF no la publica y, segun el Technical Paper de NASA DEVELOP (2022), sus
 * valores "were determined using the 2016-2017 fire season as a proxy", es decir
 * son una calibracion empirica chilena. Antes de cualquier uso operativo, la
 * matriz debe sustituirse por la de CONAF o calibrarse contra las capas PI
 * publicadas (ver conaf_api.calibrar_matriz).
 *
 * Unidad de Informacion y Analisis (UIA), CONAF.
 */

// ===========================================================================
// 0. MATRIZ RECONSTRUIDA DE PROBABILIDAD DE IGNICION (288 celdas)
//    clave = ReclassC(HCFM) + ReclassG(hillshade) + ReclassA(T)
//    Generada por generar_matriz.py. SUSTITUIR POR LA MATRIZ OFICIAL DE CONAF
//    o por la calibrada empiricamente con conaf_api.calibrar_matriz().
// ===========================================================================

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

// ===========================================================================
// 1. PARAMETROS
// ===========================================================================

var UMBRAL_PI       = 70;    // %
var UMBRAL_VIENTO   = 20;    // km/h
var HORA_INICIO     = 14;    // hora local
var HORA_FIN        = 18;    // hora local (18:00-18:59 incluida => 5 pasos)
var N_DIAS          = 5;     // d0..d4

// Chile continental: UTC-4 en horario normal, UTC-3 en horario de verano
// (primer sabado de septiembre al primer sabado de abril).
var DESFASE_UTC     = -4;

var ESCALA_INDICE   = 2000;  // m. Verificado: los poligonos publicados por CONAF
                             // equivalen a celdas de 4.000.000 m2 en EPSG:3857.
var ESCALA_ZONAL    = 500;   // m. Verificado: los valores de com_ha publicados por
                             // CONAF son todos multiplos exactos de 25 ha, es decir
                             // celdas de 500 x 500 m.

// Limite comunal oficial. Sustituir por el asset propio con la Division
// Politica Administrativa 2023 (SUBDERE/IGM/INE). Debe tener un campo con el
// codigo unico territorial y otro con el nombre.
var COMUNAS   = ee.FeatureCollection('projects/TU_PROYECTO/assets/dpa_2023_comunas');
var CAMPO_ID  = 'COMUNA';     // codigo unico territorial
var CAMPO_NOM = 'NOM_COMUNA';

// ===========================================================================
// 2. CAPAS ESTATICAS: combustible y sombreado
// ===========================================================================

// ESA WorldCover v200 (2021), 10 m. Clases consideradas superficie combustible:
// 10 bosques, 20 matorrales, 30 pastizales, 40 cultivos agricolas, 90 humedales.
var worldcover  = ee.ImageCollection('ESA/WorldCover/v200').first();
var combustible = worldcover.remap([10, 20, 30, 40, 90], [1, 1, 1, 1, 1], 0)
                            .rename('combustible');

// Sombreado topografico sobre SRTM 90 m, azimut 313 y altura solar 60 grados,
// tal como en el modelo original de CONAF en ArcGIS.
var dem       = ee.Image('CGIAR/SRTM90_V4');
var hillshade = ee.Terrain.hillshade(dem, 313, 60);
var reclassG  = hillshade.lte(123.5).multiply(200)
                  .add(hillshade.gt(123.5).multiply(100))
                  .rename('reclassG');

// ===========================================================================
// 3. PRONOSTICO GFS: ultima corrida, ventana de tarde
// ===========================================================================

var gfs = ee.ImageCollection('NOAA/GFS0P25');

var ultimaCorrida = ee.Number(
  gfs.limit(1, 'creation_time', false).first().get('creation_time'));

var corrida = gfs
  .filter(ee.Filter.eq('creation_time', ultimaCorrida))
  .filter(ee.Filter.gte('forecast_hours', 1))     // radiacion y precipitacion
  .filter(ee.Filter.lte('forecast_hours', 120));  // tramo de paso horario

// Etiqueta cada imagen con su hora y fecha en hora local de Chile.
var etiquetada = corrida.map(function (img) {
  var t = ee.Date(ee.Number(img.get('forecast_time'))).advance(DESFASE_UTC, 'hour');
  return img.set({
    hora_local:  t.get('hour'),
    fecha_local: t.format('YYYY-MM-dd')
  });
});

var ventana = etiquetada.filter(
  ee.Filter.rangeContains('hora_local', HORA_INICIO, HORA_FIN));

// ===========================================================================
// 4. CALCULO POR PASO HORARIO
// ===========================================================================

function calcularHora(img) {
  var t  = img.select('temperature_2m_above_ground');        // C
  var hr = img.select('relative_humidity_2m_above_ground');  // %
  var u  = img.select('u_component_of_wind_10m_above_ground');
  var v  = img.select('v_component_of_wind_10m_above_ground');

  // Viento a 10 m en km/h.
  var viento = u.hypot(v).multiply(3.6).rename('VV');

  // Humedad del combustible fino muerto (Universidad de Chile).
  var hcfm = hr.multiply(0.262).subtract(t.multiply(0.00982))
               .add(0.297374).rename('HC');

  // Reclass C: 1000 * ceil(HCFM), acotado a [2000, 17000].
  // Fuera del dominio (HCFM <= 0 o > 30) se enmascara, igual que el NoData
  // del Reclassify de ArcGIS en el modelo original.
  var reclassC = hcfm.ceil().clamp(2, 17).multiply(1000)
                     .updateMask(hcfm.gt(0).and(hcfm.lte(30)));

  // Reclass A: clase 1..9 de temperatura en C, con NoData sobre 40 C.
  var reclassA = t.divide(5).ceil().add(1).clamp(1, 9)
                  .updateMask(t.lte(40));

  var clave = reclassC.add(reclassG).add(reclassA).rename('clave');

  // Matriz de probabilidad de ignicion.
  var pi = clave.remap(CLAVES_PI, VALORES_PI).rename('PI');

  // Regla de activacion: Reclass D binario + Reclass F, RFW == 2.
  var rfw = pi.gte(UMBRAL_PI).add(viento.gte(UMBRAL_VIENTO)).rename('RFW');

  return ee.Image.cat([t.rename('TP'), hr.rename('HR'), hcfm, viento, pi,
                       rfw.eq(2).rename('BR')])
           .resample('bilinear')
           .set({fecha_local: img.get('fecha_local'),
                 hora_local:  img.get('hora_local'),
                 'system:time_start': img.get('forecast_time')});
}

var horario = ventana.map(calcularHora);

// ===========================================================================
// 5. AGREGACION DIARIA: numero de horas en condicion de Boton Rojo
// ===========================================================================

var fechas = ee.List(horario.aggregate_array('fecha_local')).distinct().sort()
               .slice(0, N_DIAS);

var porDia = ee.ImageCollection.fromImages(fechas.map(function (fecha) {
  var delDia = horario.filter(ee.Filter.eq('fecha_local', fecha));
  var horas  = delDia.select('BR').sum().rename('horas');
  return horas.updateMask(horas.gt(0)).updateMask(combustible)
              .set({fecha_local: fecha, n_pasos: delDia.size()});
}));

// ===========================================================================
// 6. ESTADISTICA ZONAL POR COMUNA
// ===========================================================================

var areaHa = ee.Image.pixelArea().divide(10000);

// Superficie combustible de cada comuna. CONAF publica este valor en el campo
// com_ha: se verifico que corresponde a la superficie COMBUSTIBLE y no a la
// superficie total de la comuna.
var superficieCombustible = areaHa.updateMask(combustible)
  .reduceRegions({collection: COMUNAS, reducer: ee.Reducer.sum(),
                  scale: ESCALA_ZONAL, tileScale: 4})
  .map(function (f) { return f.select([CAMPO_ID, CAMPO_NOM, 'sum'],
                                      [CAMPO_ID, CAMPO_NOM, 'com_ha']); });

function tablaDeDia(imagen) {
  imagen = ee.Image(imagen);
  var fecha = imagen.get('fecha_local');
  var horas = imagen.select('horas');

  var porHora = ee.List.sequence(1, N_DIAS).map(function (h) {
    var mascara = horas.eq(ee.Number(h));
    return areaHa.updateMask(mascara)
      .reduceRegions({collection: superficieCombustible,
                      reducer: ee.Reducer.sum(),
                      scale: ESCALA_ZONAL, tileScale: 4})
      .filter(ee.Filter.gt('sum', 0))
      .map(function (f) {
        var ha = ee.Number(f.get('sum'));
        var combustibleHa = ee.Number(f.get('com_ha'));
        return f.set({
          date:       fecha,
          horas:      h,
          SUM_br_ha:  ha,
          proportion: ha.divide(combustibleHa.max(1))
        }).select([CAMPO_ID, CAMPO_NOM, 'date', 'horas',
                   'SUM_br_ha', 'com_ha', 'proportion']);
      });
  });
  return ee.FeatureCollection(porHora).flatten();
}

var resultado = ee.FeatureCollection(porDia.toList(N_DIAS).map(tablaDeDia)).flatten();

// ===========================================================================
// 7. VISUALIZACION Y EXPORTACION
// ===========================================================================

var paletaPI = ['bf78e3', '0073ff', '00b2ff', '00eeff', '249900',
                'fbff00', 'ffcc00', 'ff9900', 'ff6600', 'f01811'];
var paletaBR = ['fff3c4', 'ffcc7a', 'ff8c3a', 'b32020', '7a0000'];

Map.setCenter(-71.3, -35.5, 6);
Map.addLayer(ee.Image(horario.select('PI').first()),
             {min: 0, max: 100, palette: paletaPI}, 'PI primera hora', false);
Map.addLayer(ee.Image(porDia.first()).select('horas'),
             {min: 1, max: 5, palette: paletaBR}, 'Horas en Boton Rojo (d0)');

print('Ultima corrida GFS (UTC):', ee.Date(ultimaCorrida));
print('Pasos horarios en ventana:', ventana.size());
print('Fechas locales cubiertas:', fechas);
print('Comunas-dia-hora resultantes:', resultado.size());
print('Primeras filas:', resultado.limit(20));

Export.table.toDrive({
  collection: resultado,
  description: 'boton_rojo_replica_uia',
  fileFormat: 'CSV',
  selectors: [CAMPO_ID, CAMPO_NOM, 'date', 'horas', 'SUM_br_ha', 'com_ha', 'proportion']
});
