import json
from pathlib import Path

p = Path("docs/generated/csv_profile.json")
with open(p, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"Total Rows: {data['n_rows']:,}")
print(f"Total Columns: {data['n_cols']}")
print(f"Exact Duplicates: {data['exact_duplicates']}")
print(f"Index Duplicates: {data['index_duplicates']}")

print("\n--- Temporadas ---")
for k, v in sorted(data['temporadas'].items()):
    print(f"  {k}: {v:,}")

print("\n--- Coordinates QA ---")
for k, v in data['coord_stats'].items():
    print(f"  {k}: {v}")

print("\n--- Area Statistics (ha) ---")
for k, v in data['area_stats'].items():
    print(f"  {k}: {v}")

print("\n--- Region Distribution ---")
for k, v in data['admin_stats'].get('region_counts', {}).items():
    print(f"  {k}: {v:,}")

print("\n--- Columns List with Null % ---")
for col in data['columns_info']:
    print(f"  {col['name']:<40} | Null: {col['null_pct']:>6.2f}% ({col['null_count']:>6,}) | Uniques: {col['unique_count']:>6,} | Samples: {col['samples'][:2]}")
