import json

p = "docs/generated/csv_profile.json"
with open(p, "r", encoding="utf-8") as f:
    d = json.load(f)

print("=== TOTALS ===")
print("Rows:", d['n_rows'])
print("Cols:", d['n_cols'])
print("Exact duplicates:", d['exact_duplicates'])
print("Index duplicates:", d['index_duplicates'])

print("\n=== TEMPORADAS ===")
for k, v in sorted(d['temporadas'].items()):
    print(f"{k}: {v}")

print("\n=== COORD STATS ===")
for k, v in d['coord_stats'].items():
    print(f"{k}: {v}")

print("\n=== AREA STATS ===")
for k, v in d['area_stats'].items():
    print(f"{k}: {v}")

print("\n=== REGIONS ===")
for k, v in d['admin_stats']['region_counts'].items():
    print(f"{k}: {v}")
