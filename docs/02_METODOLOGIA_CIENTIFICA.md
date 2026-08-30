# 02 — Metodología científica BR-HR

## 1. Baseline primero

Congelar una implementación reproducible del Botón Rojo original. El baseline sirve para:
- comprobar equivalencia;
- comparar mejoras;
- detectar regresiones;
- mantener trazabilidad institucional.

## 2. Diseño espacio-temporal

### Unidad espacial
H3 resolución 8.

### Grilla ambiental
250 m.

### BR-Window
H3×hora entre 14:00 y 18:59.

### Ignition-24h
H3×hora para 24 horas, en fase posterior.

## 3. Positivos

Evento histórico válido:
- coordenada QA aprobada;
- timestamp interpretable;
- asignación H3;
- `y_ignition=1`.

Múltiples incendios en el mismo H3×hora:
- `y_ignition=1`;
- guardar `n_events`.

## 4. Negativos

### Espaciales
Mismo día/hora; región o clima comparable; combustible; sin evento.

### Temporales
Mismo H3; hora y periodo comparable; fecha sin evento.

Ratio inicial configurable:
- 10 espaciales;
- 5 temporales.

No usar negativos obvios fuera del dominio combustible.

## 5. Corrección por case-control

Guardar probabilidad de inclusión y peso de muestreo.

Separar:
- habilidad discriminatoria;
- calibración absoluta.

La calibración final debe evaluarse sobre una muestra representativa del universo de riesgo.

## 6. Fuentes retrospectivas

### ERA5-Land
Hindcast homogéneo para 2014–2024.

### GFS
Backtest operacional desde disponibilidad histórica.

### MapBiomas Chile
Cobertura anual histórica.

### DEM
Variables topográficas.

### Landsat/Sentinel
Estado de vegetación, respetando disponibilidad temporal.

## 7. Features

### Meteorología
T, RH/dew point/VPD, viento.

### Memoria
lluvia 1h/24h/72h/7d, radiación, humedad de suelo.

### Combustible
fracciones y clase dominante.

### Vegetación
NDVI, NDMI, anomalía.

### Topografía
elevación, pendiente, aspecto, northness/eastness, TPI, exposición.

### Contexto humano
vías, asentamientos, historial pasado de incendios.

## 8. Downscaling

### Temperatura
Corrección topográfica/lapse-rate calibrada.

### Humedad
Método termodinámicamente coherente cuando sea posible.

### Viento
Exposición/rugosidad/topografía; calibración con observaciones.

WindNinja/WRF como challenger posterior.

## 9. Recalibración PI

Construir tabla empírica de riesgo por combinación:
- clase HCFM;
- clase de temperatura;
- exposición.

Comparar matriz original con `PI_CHILE`.

Realizar búsqueda de umbrales de PI y viento sin tocar el test ciego.

## 10. Modelos

Orden:
1. BR original.
2. BR recalibrado.
3. Logistic.
4. GAM.
5. Random Forest.
6. Gradient Boosting / XGBoost / LightGBM.

## 11. Splits

- Train: 2014–15 a 2020–21.
- Validation: 2021–22.
- Test ciego: 2022–23 y 2023–24.

Añadir validación espacial por región/bloques.

## 12. Métricas

- PR-AUC.
- ROC-AUC.
- Brier.
- Calibration curve.
- Recall/POD.
- False Alarm Ratio.
- CSI.
- Top 5/10/20 % territorio vs % igniciones capturadas.

## 13. Backtest operacional

Evaluar D+1 a D+5 con el forecast que realmente habría estado disponible.

## 14. Modelo de grandes incendios

Separado de ignición.

Targets sugeridos:
- >10 ha;
- >100 ha.

No usar superficie final para P-IGN.

## 15. Incertidumbre

`CONF` debe incorporar, entre otros:
- horizonte;
- datos faltantes;
- cobertura observacional;
- desempeño regional;
- distancia respecto del dominio de entrenamiento;
- acuerdo entre modelos.

Nunca usar `CONF` como sinónimo de `P_IGN`.
