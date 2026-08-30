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

# Exact boolean rasters
boton_rojo = pi.gte(60.0).And(fuel_mask).And(hcfm.lte(10.0)).unmask(0).rename('rojo')
alerta_amarilla = pi.gte(40.0).And(pi.lt(60.0)).And(fuel_mask).unmask(0).rename('amarillo')

# Load Comunas Asset in GEE
comunas_fc = ee.FeatureCollection('projects/boton-rojo-chile/assets/comunas_chile')

# Reduce regions directly in GEE
alert_img = ee.Image.cat([boton_rojo, alerta_amarilla])
reduced = alert_img.reduceRegions(
    collection=comunas_fc,
    reducer=ee.Reducer.mean(),
    scale=2500,
    tileScale=4
).getInfo()

results = []
for f in reduced.get('features', []):
    p = f['properties']
    pct_rojo = round(float(p.get('rojo', 0) or 0) * 100.0, 1)
    pct_amarillo = round(float(p.get('amarillo', 0) or 0) * 100.0, 1)
    comuna_name = p.get('comuna') or p.get('Comuna') or ''
    region_name = p.get('region') or p.get('Region') or ''
    codcom = str(p.get('cod_comuna') or p.get('codcom') or '')
    
    if pct_rojo >= 30.0:
        alerta = 'ALERTA ROJA COMUNAL'
    elif pct_amarillo >= 25.0 or pct_rojo >= 10.0 or (pct_rojo + pct_amarillo) >= 30.0:
        alerta = 'ALERTA AMARILLA COMUNAL'
    elif (pct_rojo + pct_amarillo) >= 10.0:
        alerta = 'ALERTA TEMPRANA PREVENTIVA'
    else:
        alerta = 'NORMAL'
        
    results.append({
        'comuna': comuna_name,
        'region': region_name,
        'codcom': codcom,
        'pct_rojo': pct_rojo,
        'pct_amarillo': pct_amarillo,
        'alerta': alerta
    })

df_res = pd.DataFrame(results)
print("TOTAL COMUNAS EVALUATED DIRECTLY FROM GEE RASTER:")
print(df_res['alerta'].value_counts())

print("\n--- SAMPLE COMUNAS IN VALPARAISO & SANTIAGO (SHOULD BE AMARILLO/NORMAL) ---")
print(df_res[df_res['region'].str.contains('Valp|Metro', case=False, na=False)][['comuna', 'region', 'pct_rojo', 'pct_amarillo', 'alerta']].head(10))

print("\n--- SAMPLE COMUNAS IN BIOBIO & NUBLE (SHOULD BE ROJA) ---")
print(df_res[df_res['region'].str.contains('Biob|Ñuble', case=False, na=False)][['comuna', 'region', 'pct_rojo', 'pct_amarillo', 'alerta']].head(10))
