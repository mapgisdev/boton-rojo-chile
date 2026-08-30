import json
import ee
import pandas as pd
import numpy as np

sa_file = 'insumos/boton-rojo-chile-49f6f47ffe4f.json'
with open(sa_file, 'r') as f:
    key_data = json.load(f)

credentials = ee.ServiceAccountCredentials(key_data['client_email'], key_file=sa_file)
ee.Initialize(credentials, project=key_data['project_id'])

# Exact GEE Image for 2023-02-03
start_date = ee.Date('2023-02-03')
end_date = start_date.advance(1, 'day')

era5 = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY') \
    .filterDate(start_date, end_date) \
    .filter(ee.Filter.calendarRange(17, 22, 'hour'))

era5_mean = era5.mean()
temp_c = era5_mean.select('temperature_2m').subtract(273.15).rename('temp_c')
dew_c = era5_mean.select('dewpoint_temperature_2m').subtract(273.15)

vp = dew_c.multiply(17.27).divide(dew_c.add(237.3)).exp()
vps = temp_c.multiply(17.27).divide(temp_c.add(237.3)).exp()
rh_pct = ee.Image(100).multiply(vp).divide(vps).clamp(3, 100).rename('rh_pct')

u_wind = era5_mean.select('u_component_of_wind_10m')
v_wind = era5_mean.select('v_component_of_wind_10m')
wind_kmh = u_wind.hypot(v_wind).multiply(3.6).rename('wind_kmh')

hcfm = rh_pct.multiply(0.20).add(ee.Image(100).subtract(temp_c).multiply(0.05)).clamp(1.0, 30.0).rename('hcfm')

pi = temp_c.multiply(1.2).add(ee.Image(100).subtract(rh_pct).multiply(0.6)).add(wind_kmh.multiply(0.8)).subtract(hcfm.multiply(2.5)).clamp(0, 100).rename('pi')

world_cover = ee.ImageCollection('ESA/WorldCover/v100').first()
fuel_mask = world_cover.eq(10).Or(world_cover.eq(20)).Or(world_cover.eq(30)).Or(world_cover.eq(40)).Or(world_cover.eq(90))

boton_rojo = pi.gte(60.0).And(fuel_mask).And(hcfm.lte(10.0)).rename('boton_rojo')
alerta_amarilla = pi.gte(40.0).And(pi.lt(60.0)).And(fuel_mask).rename('alerta_amarilla')

combined = ee.Image.cat([temp_c, rh_pct, wind_kmh, hcfm, pi, boton_rojo, alerta_amarilla])

cities = [
    ('Chillan', -72.10, -36.60),
    ('Los Angeles', -72.35, -37.47),
    ('Puren', -73.08, -38.03),
    ('Angol', -72.71, -37.80),
    ('Valparaiso', -71.62, -33.04),
    ('Santiago', -70.65, -33.45),
    ('Coquimbo', -71.25, -29.90),
    ('Talca', -71.65, -35.43),
    ('Concepcion', -73.05, -36.82),
    ('Temuco', -72.59, -38.74),
    ('Puerto Montt', -72.93, -41.47)
]

fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([lon, lat]), {'name': name}) for name, lon, lat in cities])
res = combined.reduceRegions(collection=fc, reducer=ee.Reducer.first(), scale=1000).getInfo()

print("\n--- GEE EXACT RASTER SAMPLING FOR 2023-02-03 ---")
for f in res.get('features', []):
    p = f['properties']
    print(f" -> {p.get('name')}: T={p.get('temp_c'):.1f}C | RH={p.get('rh_pct'):.1f}% | V={p.get('wind_kmh'):.1f}km/h | HCFM={p.get('hcfm'):.1f}% | PI={p.get('pi'):.1f}% -> ROJO={p.get('boton_rojo')}, AMARILLO={p.get('alerta_amarilla')}")
