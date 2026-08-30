import pandas as pd
import numpy as np

df = pd.read_csv('insumos/Consolidado_incendios_2014_2024_temporada.csv', sep=';', encoding='utf-8', low_memory=False)

def parse_num(col):
    if df[col].dtype == object:
        return pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce')
    return pd.to_numeric(df[col], errors='coerce')

lat = parse_num('Lat Calculada')
lon = parse_num('Lon Calculada')

print('=== LAT / LON OUTLIERS ===')
bad_mask = lat.isna() | lon.isna() | (lat < -56.5) | (lat > -17.5) | (lon < -110.0) | (lon > -66.0)
print(f"Total invalid / outlier coordinates: {bad_mask.sum()} / {len(df)}")
bad_df = df[bad_mask][['index', 'Región', 'Comuna', 'Coord. operativas Lat', 'Coord. operativas Lon', 'Lat Calculada', 'Lon Calculada']]
print(bad_df.to_string())

print('\n=== INICIO DATE TIME & BR WINDOW ===')
dt_inicio = pd.to_datetime(df['Inicio'], errors='coerce')
print('Null inicio:', dt_inicio.isna().sum())
print('Min inicio:', dt_inicio.min())
print('Max inicio:', dt_inicio.max())

hours = dt_inicio.dt.hour
br_window = (hours >= 14) & (hours <= 18)
print(f"Fires in BR window (14:00-18:59): {br_window.sum()} ({br_window.mean()*100:.2f}%)")
print(f"Fires outside BR window: {(~br_window).sum()} ({(~br_window).mean()*100:.2f}%)")

print('\n=== HOURLY DISTRIBUTION OF INICIO ===')
for h, count in hours.value_counts().sort_index().items():
    print(f"  Hour {h:02d}:00 -> {count:5d} ({count/len(df)*100:5.2f}%) {'[BR-WINDOW]' if 14 <= h <= 18 else ''}")

print('\n=== TEMPORAL SPLITS ===')
# Train: 2014-15 to 2020-21 (7 seasons)
# Val: 2021-22 (1 season)
# Blind Test: 2022-23 and 2023-24 (2 seasons)
train_seasons = ['2014 al 2015', '2015 al 2016', '2016 al 2017', '2017 al 2018', '2018 al 2019', '2019 al 2020', '2020 al 2021']
val_seasons = ['2021 al 2022']
test_seasons = ['2022 al 2023', '2023 al 2024']

n_train = df['temporada'].isin(train_seasons).sum()
n_val = df['temporada'].isin(val_seasons).sum()
n_test = df['temporada'].isin(test_seasons).sum()
print(f"TRAIN (2014-2021): {n_train:,} fires ({n_train/len(df)*100:.2f}%)")
print(f"VAL (2021-2022):   {n_val:,} fires ({n_val/len(df)*100:.2f}%)")
print(f"TEST (2022-2024):  {n_test:,} fires ({n_test/len(df)*100:.2f}%)")

print('\n=== TIMESTAMPS CHRONOLOGY QA (Inconsistencies) ===')
# Check chronological order: Inicio <= Detección <= Aviso <= Despacho <= Arribo <= Primer ataque <= Control <= Extinción
ts_cols = ['Inicio', 'Detección', 'Aviso', 'Despacho', 'Salida', 'Arribo', 'Primer ataque', 'Control', 'Extinción']
dts = {col: pd.to_datetime(df[col], errors='coerce') for col in ts_cols}

if_det_before_ini = (dts['Detección'] < dts['Inicio']) & dts['Detección'].notna() & dts['Inicio'].notna()
if_avi_before_det = (dts['Aviso'] < dts['Detección']) & dts['Aviso'].notna() & dts['Detección'].notna()
if_ctrl_before_ini = (dts['Control'] < dts['Inicio']) & dts['Control'].notna() & dts['Inicio'].notna()
if_ext_before_ctrl = (dts['Extinción'] < dts['Control']) & dts['Extinción'].notna() & dts['Control'].notna()

print(f"Detección before Inicio: {if_det_before_ini.sum()}")
print(f"Aviso before Detección:   {if_avi_before_det.sum()}")
print(f"Control before Inicio:    {if_ctrl_before_ini.sum()}")
print(f"Extinción before Control: {if_ext_before_ctrl.sum()}")

print('\n=== INITIAL FUEL DISTRIBUTION ===')
print(df['Combustible inicial'].value_counts(dropna=False))

print('\n=== CAUSE GENERAL DISTRIBUTION ===')
print(df['Causa General'].value_counts(dropna=False).head(10))

print('\n=== CODCOM QA ===')
print("Unique codcom:", df['Codcom'].nunique())
print("Null codcom:", df['Codcom'].isna().sum())
print("Sample codcom:", df['Codcom'].unique()[:10])
