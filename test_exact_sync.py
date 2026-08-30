import json
import ee
import pandas as pd

sa_file = 'insumos/boton-rojo-chile-49f6f47ffe4f.json'
with open(sa_file, 'r') as f:
    key_data = json.load(f)

credentials = ee.ServiceAccountCredentials(key_data['client_email'], key_file=sa_file)
ee.Initialize(credentials, project=key_data['project_id'])

# Exact single-day ERA5 for 2023-02-03 (24h)
startDate = ee.Date('2023-02-03')
endDate = startDate.advance(1, 'day')

era5 = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY') \
    .filterDate(startDate, endDate) \
    .filter(ee.Filter.calendarRange(17, 22, 'hour'))

era5Mean = era5.mean()
tempC = era5Mean.select('temperature_2m').subtract(273.15).rename('temp_c')
dewC = era5Mean.select('dewpoint_temperature_2m').subtract(273.15)

vp = dew_c = dewC.multiply(17.27).divide(dewC.add(237.3)).exp()
vps = tempC.multiply(17.27).divide(tempC.add(237.3)).exp()
rhPct = ee.Image(100).multiply(vp).divide(vps).clamp(3, 100).rename('rh_pct')

uWind = era5Mean.select('u_component_of_wind_10m')
vWind = era5Mean.select('v_component_of_wind_10m')
windKmh = uWind.hypot(vWind).multiply(3.6).rename('wind_kmh')

hcfm = rhPct.multiply(0.20).add(ee.Image(100).subtract(tempC).multiply(0.05)).clamp(1.0, 30.0).rename('hcfm')
pi = tempC.multiply(1.2).add(ee.Image(100).subtract(rhPct).multiply(0.6)).add(windKmh.multiply(0.8)).subtract(hcfm.multiply(2.5)).clamp(0, 100).rename('pi')

worldCover = ee.ImageCollection('ESA/WorldCover/v100').first()
fuelMask = worldCover.eq(10).Or(worldCover.eq(20)).Or(worldCover.eq(30)).Or(worldCover.eq(40)).Or(worldCover.eq(90))

botonRojo = pi.gte(60.0).And(fuelMask).And(hcfm.lte(10.0)).unmask(0).rename('rojo')
alertaAmarilla = pi.gte(40.0).And(pi.lt(60.0)).And(fuelMask).unmask(0).rename('amarillo')
alertaTotal = botonRojo.Or(alertaAmarilla).unmask(0).rename('total')

comunas_fc = ee.FeatureCollection('projects/boton-rojo-chile/assets/comunas_chile')
alertImg = ee.Image.cat([botonRojo, alertaAmarilla, alertaTotal])

reduced = alertImg.reduceRegions(
    collection=comunas_fc,
    reducer=ee.Reducer.mean(),
    scale=2500,
    tileScale=4
)

comunasRojas = reduced.filter(ee.Filter.gte('rojo', 0.30))
comunasAmarillas = reduced.filter(
    ee.Filter.And(
        ee.Filter.lt('rojo', 0.30),
        ee.Filter.Or(
            ee.Filter.gte('amarillo', 0.25),
            ee.Filter.gte('rojo', 0.10),
            ee.Filter.gte('total', 0.30)
        )
    )
)

print(f"GEE Exact Evaluation: Red = {comunasRojas.size().getInfo()} | Yellow = {comunasAmarillas.size().getInfo()}")
