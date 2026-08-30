#!/usr/bin/env python3
"""
profile_dataset.py — Perfil estructural y QA/QC no destructivo del consolidado de incendios 2014-2024.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
INPUT_CSV = ROOT / "insumos" / "Consolidado_incendios_2014_2024_temporada.csv"
OUT_DIR = ROOT / "docs" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def parse_chilean_number(val: Any) -> float:
    if pd.isna(val) or val is None or val == "":
        return np.nan
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return np.nan


def main() -> None:
    print(f"Reading {INPUT_CSV}...")
    df = pd.read_csv(INPUT_CSV, sep=";", encoding="utf-8", low_memory=False)
    n_rows, n_cols = df.shape
    print(f"Loaded {n_rows:,} rows, {n_cols} columns.")

    # Basic overview
    columns_info = []
    for col in df.columns:
        s = df[col]
        null_count = int(s.isna().sum())
        non_null_count = n_rows - null_count
        unique_count = int(s.nunique(dropna=True))
        sample_vals = [str(x) for x in s.dropna().unique()[:5]]
        columns_info.append({
            "name": col,
            "null_count": null_count,
            "null_pct": round(null_count / n_rows * 100, 2),
            "unique_count": unique_count,
            "samples": sample_vals,
            "dtype": str(s.dtype)
        })

    # Duplicates analysis
    exact_duplicates = int(df.duplicated().sum())
    index_duplicates = int(df["index"].duplicated().sum()) if "index" in df.columns else None

    # Temporal analysis
    temporadas = df["Temporada"].value_counts(dropna=False).to_dict() if "Temporada" in df.columns else {}
    
    # Coordinate analysis
    lat_col = "Lat Calculada" if "Lat Calculada" in df.columns else None
    lon_col = "Lon Calculada" if "Lon Calculada" in df.columns else None
    
    coord_stats = {}
    if lat_col and lon_col:
        lat_s = df[lat_col].apply(parse_chilean_number)
        lon_s = df[lon_col].apply(parse_chilean_number)
        
        lat_null = int(lat_s.isna().sum())
        lon_null = int(lon_s.isna().sum())
        
        lat_in_chile = (lat_s >= -56.5) & (lat_s <= -17.5)
        lon_in_chile = (lon_s >= -110.0) & (lon_s <= -66.0)
        valid_coords = lat_in_chile & lon_in_chile & lat_s.notna() & lon_s.notna()
        
        lat_out_bounds = int((~lat_in_chile & lat_s.notna()).sum())
        lon_out_bounds = int((~lon_in_chile & lon_s.notna()).sum())

        coord_stats = {
            "lat_col": lat_col,
            "lon_col": lon_col,
            "lat_min": float(lat_s.min()) if lat_s.notna().any() else None,
            "lat_max": float(lat_s.max()) if lat_s.notna().any() else None,
            "lat_mean": float(lat_s.mean()) if lat_s.notna().any() else None,
            "lon_min": float(lon_s.min()) if lon_s.notna().any() else None,
            "lon_max": float(lon_s.max()) if lon_s.notna().any() else None,
            "lon_mean": float(lon_s.mean()) if lon_s.notna().any() else None,
            "lat_null": lat_null,
            "lon_null": lon_null,
            "valid_within_chile_count": int(valid_coords.sum()),
            "valid_within_chile_pct": round(float(valid_coords.mean() * 100), 2),
            "lat_out_bounds": lat_out_bounds,
            "lon_out_bounds": lon_out_bounds
        }

    # Administrative breakdown
    admin_stats = {}
    if "Región" in df.columns:
        admin_stats["region_counts"] = {str(k): int(v) for k, v in df["Región"].value_counts(dropna=False).items()}
    if "Codcom" in df.columns:
        admin_stats["codcom_nulls"] = int(df["Codcom"].isna().sum())
        admin_stats["codcom_uniques"] = int(df["Codcom"].nunique())

    # Area analysis
    area_stats = {}
    total_area_col = "Superficie total" if "Superficie total" in df.columns else (
        "Superficie" if "Superficie" in df.columns else None
    )
    if total_area_col:
        area_s = df[total_area_col].apply(parse_chilean_number)
        area_stats = {
            "total_area_col": total_area_col,
            "min_ha": float(area_s.min()),
            "max_ha": float(area_s.max()),
            "median_ha": float(area_s.median()),
            "mean_ha": float(area_s.mean()),
            "p90_ha": float(area_s.quantile(0.90)),
            "p95_ha": float(area_s.quantile(0.95)),
            "p99_ha": float(area_s.quantile(0.99)),
            "count_gt0": int((area_s > 0).sum()),
            "count_eq0": int((area_s == 0).sum()),
            "count_gt10ha": int((area_s > 10).sum()),
            "count_gt50ha": int((area_s > 50).sum()),
            "count_gt100ha": int((area_s > 100).sum()),
            "count_gt1000ha": int((area_s > 1000).sum()),
            "total_sum_ha": float(area_s.sum())
        }

    # Fuel and Causes
    fuel_cols = [c for c in df.columns if "combustible" in c.lower() or "vegetacion" in c.lower()]
    cause_cols = [c for c in df.columns if "causa" in c.lower() or "origen" in c.lower()]
    
    fuel_stats = {}
    for fc in fuel_cols:
        fuel_stats[fc] = {str(k): int(v) for k, v in df[fc].value_counts(dropna=False).head(15).items()}
        
    cause_stats = {}
    for cc in cause_cols:
        cause_stats[cc] = {str(k): int(v) for k, v in df[cc].value_counts(dropna=False).head(15).items()}

    # Meteorology fields
    met_cols = [c for c in df.columns if any(k in c.lower() for k in ["temp", "hum", "viento", "direcc", "veloc"])]
    met_stats = {}
    for mc in met_cols:
        numeric_s = df[mc].apply(parse_chilean_number)
        met_stats[mc] = {
            "null_count": int(df[mc].isna().sum()),
            "null_pct": round(int(df[mc].isna().sum()) / n_rows * 100, 2),
            "min": float(numeric_s.min()) if numeric_s.notna().any() else None,
            "max": float(numeric_s.max()) if numeric_s.notna().any() else None,
            "mean": float(numeric_s.mean()) if numeric_s.notna().any() else None,
            "median": float(numeric_s.median()) if numeric_s.notna().any() else None,
        }

    # Timestamps & Operational times
    time_cols = [c for c in df.columns if any(k in c.lower() for k in ["inicio", "detecci", "aviso", "llegada", "control", "extin", "fecha", "hora"])]
    
    report = {
        "n_rows": n_rows,
        "n_cols": n_cols,
        "exact_duplicates": exact_duplicates,
        "index_duplicates": index_duplicates,
        "temporadas": {str(k): int(v) for k, v in temporadas.items()},
        "coord_stats": coord_stats,
        "admin_stats": admin_stats,
        "area_stats": area_stats,
        "fuel_stats": fuel_stats,
        "cause_stats": cause_stats,
        "met_stats": met_stats,
        "time_cols": time_cols,
        "columns_info": columns_info
    }

    out_file = OUT_DIR / "csv_profile.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Report saved to {out_file}")


if __name__ == "__main__":
    main()
