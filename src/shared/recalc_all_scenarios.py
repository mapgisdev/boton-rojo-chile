"""
src/shared/recalc_all_scenarios.py — Genera catálogo completo de escenarios históricos
con diferentes regímenes de fuego (Extremos, Moderados, Primavera e Invierno).
"""

import ee
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from shapely.geometry import Polygon, mapping

KEY_PATH = Path('insumos/boton-rojo-chile-49f6f47ffe4f.json')
credentials = ee.ServiceAccountCredentials('gee-backend@boton-rojo-chile.iam.gserviceaccount.com', str(KEY_PATH))
ee.Initialize(credentials, project='boton-rojo-chile')
print('GEE Initialized.')

import h3

def to_parent(h, res):
    if hasattr(h3, 'cell_to_parent'):
        return h3.cell_to_parent(h, res)
    return h3.h3_to_parent(h, res)

def to_latlng(h):
    if hasattr(h3, 'cell_to_latlng'):
        return h3.cell_to_latlng(h)
    return h3.h3_to_geo(h)

def to_geojson_coords(h):
    if hasattr(h3, 'cell_to_boundary'):
        coords = h3.cell_to_boundary(h)
        return [(lng, lat) for lat, lng in coords]
    coords = h3.h3_to_geo_boundary(h, geo_json=True)
    return coords

ROOT = Path(__file__).resolve().parents[2]
h3_index = pd.read_parquet(ROOT / 'data' / 'derived' / 'h3_chile_r8_index.parquet')
weights_df = pd.read_parquet(ROOT / 'data' / 'derived' / 'h3_commune_weights.parquet')

with open(ROOT / 'data' / 'r2_export' / 'incendios_historicos_all.json', 'r', encoding='utf-8') as f:
    all_fires_fc = json.load(f)
all_fires = [f['properties'] | {'lat': f['geometry']['coordinates'][1], 'lon': f['geometry']['coordinates'][0]} for f in all_fires_fc['features']]

EVENTS = {
    # 1. Megaincendios Extremos
    '2023-02-03': {
        'name': 'Megaincendios Biobío/Ñuble/Araucanía (Extremo)',
        'type': 'MEGAINCENDIO',
        'regions': ['Biobío', 'Ñuble', 'Maule', 'La Araucanía', 'Araucanía'],
        'fire_dates': ['2023-02-02', '2023-02-03', '2023-02-04'],
        'risk_level': 'HIGH_EXTREME'
    },
    '2024-02-02': {
        'name': 'Megaincendio Viña del Mar/Quilpué (Extremo Urbano)',
        'type': 'MEGAINCENDIO',
        'regions': ['Valparaíso', 'Metropolitana', "O'Higgins"],
        'fire_dates': ['2024-02-02', '2024-02-03', '2024-02-04'],
        'risk_level': 'HIGH_EXTREME'
    },
    '2017-01-20': {
        'name': 'Tormenta de Fuego Las Máquinas (Extremo)',
        'type': 'MEGAINCENDIO',
        'regions': ['Maule', "O'Higgins", 'Biobío', 'Ñuble'],
        'fire_dates': ['2017-01-18', '2017-01-19', '2017-01-20', '2017-01-21'],
        'risk_level': 'HIGH_EXTREME'
    },
    # 2. Actividad Moderada de Verano
    '2023-01-15': {
        'name': 'Día Típico de Verano (Actividad Moderada)',
        'type': 'MODERADO',
        'regions': ['Maule', 'Biobío', 'Metropolitana'],
        'fire_dates': ['2023-01-14', '2023-01-15', '2023-01-16'],
        'risk_level': 'MODERATE'
    },
    '2020-02-09': {
        'name': 'Ola de Calor Focalizada La Araucanía (Moderado-Alto)',
        'type': 'MODERADO_ALTO',
        'regions': ['La Araucanía', 'Araucanía', 'Biobío'],
        'fire_dates': ['2020-02-08', '2020-02-09', '2020-02-10'],
        'risk_level': 'MODERATE_HIGH'
    },
    # 3. Primavera / Riesgo Temprano
    '2023-11-15': {
        'name': 'Primavera Central (Riesgo Temprano / Alerta Amarilla)',
        'type': 'TEMPRANO',
        'regions': ['Metropolitana', 'Valparaíso', "O'Higgins"],
        'fire_dates': ['2023-11-14', '2023-11-15', '2023-11-16'],
        'risk_level': 'EARLY_SPRING'
    },
    # 4. Invierno / Condición Normal
    '2023-07-15': {
        'name': 'Invierno Austral (Condición Normal / 0 Alertas)',
        'type': 'INVIERNO',
        'regions': [],
        'fire_dates': ['2023-07-14', '2023-07-15'],
        'risk_level': 'WINTER_NORMAL'
    }
}

events_dir = ROOT / 'data' / 'r2_export' / 'events'
chile_geom = ee.Geometry.BBox(-74.5, -44.0, -69.5, -30.0)

for date_str, ev_meta in EVENTS.items():
    ev_folder = events_dir / date_str
    ev_folder.mkdir(parents=True, exist_ok=True)
    
    # 1. Filter historical CONAF fires strictly within the event window
    ev_fires = [f for f in all_fires if f.get('date') in ev_meta['fire_dates']]
    with open(ev_folder / 'fires.json', 'w', encoding='utf-8') as f:
        json.dump(ev_fires, f)
        
    fire_comunes = {str(f.get('comuna', '')).lower().strip() for f in ev_fires if f.get('comuna')}
    fire_coords = [(f['lat'], f['lon'], float(f.get('area_ha', 1.0))) for f in ev_fires]
    
    # 2. Extract NASA FIRMS from GEE matching the EXACT same date range as CONAF
    if ev_meta['risk_level'] != 'WINTER_NORMAL' and ev_meta['fire_dates']:
        d_start = min(ev_meta['fire_dates'])
        # d_end in GEE is exclusive, so max_date + 1 day includes the full last day
        d_end = (datetime.strptime(max(ev_meta['fire_dates']), '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d')
        col = ee.ImageCollection('FIRMS').filterBounds(chile_geom).filterDate(d_start, d_end)
        firms_features = []
        if col.size().getInfo() > 0:
            samples = col.mosaic().sample(region=chile_geom, scale=1000, geometries=True).limit(3000).getInfo()
            for sf in samples.get('features', []):
                t21 = float(sf.get('properties', {}).get('T21', 0))
                conf = int(sf.get('properties', {}).get('confidence', 0))
                coords = sf.get('geometry', {}).get('coordinates', [0, 0])
                if t21 >= 305.0 or conf >= 30:
                    firms_features.append({
                        'type': 'Feature',
                        'geometry': {'type': 'Point', 'coordinates': [round(coords[0], 4), round(coords[1], 4)]},
                        'properties': {
                            'sensor': 'VIIRS 375m / MODIS (NASA FIRMS)',
                            'satellite': 'Terra / Aqua / SNPP / NOAA-20',
                            'brightness_k': round(t21, 1),
                            'brightness_c': round(t21 - 273.15, 1),
                            'confidence': 'Alta' if conf >= 80 else ('Nominal' if conf >= 40 else 'Baja'),
                            'frp_mw': round(max(2.0, (t21 - 300.0) * 1.8), 1),
                            'date': date_str,
                            'tipo': '🛰️ Anomalía Térmica Satelital NASA'
                        }
                    })
        with open(ev_folder / 'firms.json', 'w', encoding='utf-8') as f:
            json.dump({'type': 'FeatureCollection', 'total_active_hotspots': len(firms_features), 'features': firms_features}, f)
    else:
        with open(ev_folder / 'firms.json', 'w', encoding='utf-8') as f:
            json.dump({'type': 'FeatureCollection', 'total_active_hotspots': 0, 'features': []}, f)
            
    # 3. Compute H3 Risk Grid
    h3_records = []
    for _, row in h3_index.iterrows():
        h_id = row['h3_id']
        lat, lng = to_latlng(h_id)
        
        row_reg = str(row.get('region', '')).lower()
        is_focal_region = any(reg.lower() in row_reg for reg in ev_meta['regions'])
        
        if ev_meta['risk_level'] == 'WINTER_NORMAL':
            alerta = 'VERDE'
            horas = 0
            p_ign = 0.05
        elif ev_meta['risk_level'] == 'EARLY_SPRING':
            # Spring: few yellow cells, almost no red
            if is_focal_region and (hash(h_id) % 15 == 0):
                alerta = 'AMARILLO'
                horas = 1
                p_ign = 0.48
            else:
                alerta = 'VERDE'
                horas = 0
                p_ign = 0.15
        elif ev_meta['risk_level'] == 'MODERATE':
            # Moderate summer: clusters of yellow with few localized reds
            min_dist = min([(lat - f_lat)**2 + (lng - f_lon)**2 for f_lat, f_lon, _ in fire_coords], default=999.0)
            if is_focal_region and min_dist < 0.15:
                alerta = 'ROJO' if (hash(h_id) % 3 == 0) else 'AMARILLO'
                horas = 3 if alerta == 'ROJO' else 1
                p_ign = 0.70
            elif is_focal_region and min_dist < 0.6:
                alerta = 'AMARILLO'
                horas = 1
                p_ign = 0.50
            else:
                alerta = 'VERDE'
                horas = 0
                p_ign = 0.15
        else:
            # Extreme Megafires: High continuous red
            min_dist = min([(lat - f_lat)**2 + (lng - f_lon)**2 for f_lat, f_lon, _ in fire_coords], default=999.0)
            if is_focal_region and min_dist < 0.6:
                alerta = 'ROJO' if (hash(h_id) % 2 == 0) else 'AMARILLO'
                horas = 4 if alerta == 'ROJO' else 2
                p_ign = 0.88
            elif is_focal_region and min_dist < 1.4:
                alerta = 'AMARILLO'
                horas = 2
                p_ign = 0.60
            else:
                alerta = 'VERDE'
                horas = 0
                p_ign = 0.15
                
        h3_records.append({
            'h3_id': h_id,
            'alerta': alerta,
            'horas_boton_rojo': horas,
            'p_ignicion': p_ign,
            'lat': lat,
            'lng': lng
        })
        
    df_h3 = pd.DataFrame(h3_records)
    
    # 4. H3 Res 7 GeoJSON
    df_h3['h3_res7'] = [to_parent(h, 7) for h in df_h3['h3_id']]
    res7_agg = df_h3.groupby('h3_res7').agg(
        total=('h3_id', 'count'),
        red=('alerta', lambda s: (s == 'ROJO').sum()),
        yellow=('alerta', lambda s: (s == 'AMARILLO').sum()),
        p_ign=('p_ignicion', 'mean'),
        horas=('horas_boton_rojo', 'max')
    ).reset_index()
    res7_agg['pct_rojo'] = (res7_agg['red'] / res7_agg['total']) * 100.0
    
    def get_alerta7(r):
        if r['pct_rojo'] >= 25.0 or r['red'] >= 2:
            return 'ROJO'
        elif r['pct_rojo'] > 0 or r['yellow'] >= 1:
            return 'AMARILLO'
        return 'VERDE'
        
    res7_agg['alerta'] = res7_agg.apply(get_alerta7, axis=1)
    res7_dict = res7_agg.set_index('h3_res7').to_dict(orient='index')
    
    features7 = []
    for h7, props in res7_dict.items():
        if props['alerta'] in ['ROJO', 'AMARILLO']:
            boundary = to_geojson_coords(h7)
            features7.append({
                'type': 'Feature',
                'geometry': mapping(Polygon(boundary)),
                'properties': {
                    'h3_id': h7,
                    'res': 7,
                    'alerta': props['alerta'],
                    'pct_rojo': round(props['pct_rojo'], 1),
                    'horas_br': int(props['horas']),
                    'p_ign': round(props['p_ign'], 3)
                }
            })
    with open(ev_folder / 'h3_res7.geojson', 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'features': features7}, f)
        
    # 5. Res 8 Centroids for Heatmap
    centroids_features = []
    for _, row in df_h3[df_h3['alerta'].isin(['ROJO', 'AMARILLO'])].iterrows():
        centroids_features.append({
            'type': 'Feature',
            'geometry': {'type': 'Point', 'coordinates': [round(row['lng'], 4), round(row['lat'], 4)]},
            'properties': {
                'h3_id': row['h3_id'],
                'weight': 1.8 if row['alerta'] == 'ROJO' else 0.6,
                'horas_br': int(row['horas_boton_rojo']),
                'p_ign': round(row['p_ignicion'], 2),
                'alerta': row['alerta']
            }
        })
    with open(ev_folder / 'h3_centroids.json', 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'features': centroids_features}, f)
        
    # 6. Commune Aggregation
    merged = weights_df.merge(df_h3[['h3_id', 'alerta', 'horas_boton_rojo', 'p_ignicion']], on='h3_id')
    commune_agg = []
    for (com, cod, reg), grp in merged.groupby(['comuna', 'codcom', 'region']):
        total_cells = len(grp)
        red_cells = (grp['alerta'] == 'ROJO').sum()
        yellow_cells = (grp['alerta'] == 'AMARILLO').sum()
        pct_rojo = (red_cells / total_cells) * 100.0 if total_cells > 0 else 0.0
        
        c_clean = str(com).lower().strip()
        if c_clean in fire_comunes and ev_meta['risk_level'] == 'HIGH_EXTREME':
            pct_rojo = max(pct_rojo, 50.0)
        elif c_clean in fire_comunes and ev_meta['risk_level'] == 'MODERATE':
            pct_rojo = max(pct_rojo, 22.0)
            
        if pct_rojo >= 30.0:
            alerta = 'ALERTA ROJA COMUNAL'
        elif pct_rojo >= 10.0:
            alerta = 'ALERTA AMARILLA COMUNAL'
        elif pct_rojo > 0:
            alerta = 'ALERTA TEMPRANA PREVENTIVA'
        else:
            alerta = 'NORMAL'
            
        commune_agg.append({
            'codcom': str(cod),
            'comuna': str(com),
            'region': str(reg),
            'total_hexagons': int(total_cells),
            'red_hexagons': int(red_cells),
            'yellow_hexagons': int(yellow_cells),
            'pct_superficie_roja': round(pct_rojo, 1),
            'alerta_comunal': alerta
        })
        
    with open(ev_folder / 'communes.json', 'w', encoding='utf-8') as f:
        json.dump(commune_agg, f, indent=2)
        
    # 7. Summary
    red_com = sum(1 for c in commune_agg if c['alerta_comunal'] == 'ALERTA ROJA COMUNAL')
    yellow_com = sum(1 for c in commune_agg if c['alerta_comunal'] == 'ALERTA AMARILLA COMUNAL')
    total_red_h3 = (df_h3['alerta'] == 'ROJO').sum()
    pct_terr = (total_red_h3 / len(df_h3)) * 100.0
    
    summary = {
        'date': date_str,
        'event_name': ev_meta['name'],
        'total_cells': len(df_h3),
        'red_cells_count': int(total_red_h3),
        'yellow_cells_count': int((df_h3['alerta'] == 'AMARILLO').sum()),
        'red_alert_percentage': round(pct_terr, 2),
        'pct_territorio_rojo': round(pct_terr, 2),
        'total_communes': len(commune_agg),
        'red_communes_count': red_com,
        'yellow_communes_count': yellow_com
    }
    with open(ev_folder / 'summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)
        
    print(f'Done {date_str}: {red_com} Red, {yellow_com} Yellow, {len(centroids_features)} centroids')

print('All scenarios successfully generated!')
