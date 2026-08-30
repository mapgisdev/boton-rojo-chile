#!/usr/bin/env python3
"""Verificación no destructiva de los insumos originales de BR-HR."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
INPUT_DIR = ROOT / "insumos"
ZIP_NAME = "Boton_Rojo.zip"
CSV_NAME = "Consolidado_incendios_2014_2024_temporada(1).csv"
OUT_DIR = ROOT / "docs" / "generated"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_csv(path: Path) -> dict:
    raw = path.read_bytes()[:200_000]
    encoding = "utf-8"
    text = None
    for candidate in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            text = raw.decode(candidate)
            encoding = candidate
            break
        except UnicodeDecodeError:
            pass
    if text is None:
        raise RuntimeError("No se pudo detectar una codificación básica del CSV.")

    sample = text[:100_000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=";,|\t,")
        delimiter = dialect.delimiter
    except csv.Error:
        delimiter = ";"

    first_line = sample.splitlines()[0] if sample.splitlines() else ""
    columns = next(csv.reader([first_line], delimiter=delimiter), [])
    return {
        "encoding_detected": encoding,
        "delimiter_detected": delimiter,
        "column_count_from_header": len(columns),
        "columns": columns,
    }


def inspect_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        files = [n for n in names if not n.endswith("/")]
        return {
            "member_count": len(names),
            "file_count": len(files),
            "members": names,
        }


def main() -> None:
    zip_path = INPUT_DIR / ZIP_NAME
    csv_path = INPUT_DIR / CSV_NAME

    missing = [str(p) for p in (zip_path, csv_path) if not p.exists()]
    if missing:
        print("FALTAN INSUMOS:")
        for p in missing:
            print(" -", p)
        raise SystemExit(2)

    report = {
        "inputs": {
            ZIP_NAME: {
                "path": str(zip_path.relative_to(ROOT)),
                "size_bytes": zip_path.stat().st_size,
                "sha256": sha256(zip_path),
                "zip": inspect_zip(zip_path),
            },
            CSV_NAME: {
                "path": str(csv_path.relative_to(ROOT)),
                "size_bytes": csv_path.stat().st_size,
                "sha256": sha256(csv_path),
                "csv": detect_csv(csv_path),
            },
        }
    }

    json_path = OUT_DIR / "input_verification.json"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [
        "# Verificación de insumos",
        "",
        "Generado de manera no destructiva.",
        "",
    ]
    for name, info in report["inputs"].items():
        md += [
            f"## {name}",
            f"- Tamaño: `{info['size_bytes']}` bytes",
            f"- SHA-256: `{info['sha256']}`",
        ]
        if "zip" in info:
            md += [
                f"- Miembros ZIP: `{info['zip']['member_count']}`",
                f"- Archivos ZIP: `{info['zip']['file_count']}`",
                "",
                "### Inventario ZIP",
                "```text",
                *info["zip"]["members"],
                "```",
            ]
        if "csv" in info:
            csv_info = info["csv"]
            md += [
                f"- Encoding detectado: `{csv_info['encoding_detected']}`",
                f"- Separador detectado: `{csv_info['delimiter_detected']}`",
                f"- Columnas en cabecera: `{csv_info['column_count_from_header']}`",
                "",
                "### Columnas",
                "```text",
                *csv_info["columns"],
                "```",
            ]
        md.append("")

    (OUT_DIR / "input_verification.md").write_text("\n".join(md), encoding="utf-8")
    print(f"OK: {json_path}")
    print(f"OK: {OUT_DIR / 'input_verification.md'}")


if __name__ == "__main__":
    main()
