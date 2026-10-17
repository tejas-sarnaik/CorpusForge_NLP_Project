"""CSV and JSON Lines ingestion with explicit schema checks."""
import csv
import json
from pathlib import Path


def read_rows(path, text_column="text", split_column="split", id_column="id"):
    """Read UTF-8 CSV/JSONL records; preserve input order and non-text metadata."""
    path = Path(path)
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames or text_column not in reader.fieldnames:
                raise ValueError(f"CSV requires text column {text_column!r}")
            rows = list(reader)
    elif path.suffix.lower() in {".jsonl", ".ndjson"}:
        rows = []
        with path.open("r", encoding="utf-8-sig") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON at line {line_number}: {exc}") from exc
                if not isinstance(row, dict):
                    raise ValueError(f"JSONL line {line_number} is not an object")
                rows.append(row)
    else:
        raise ValueError("Supported inputs: .csv, .jsonl, .ndjson")
    for i, row in enumerate(rows):
        if text_column not in row:
            raise ValueError(f"Record {i+1} missing {text_column!r}")
        if not isinstance(row[text_column], str):
            raise ValueError(f"Record {i+1}: {text_column!r} must be a string")
        row.setdefault(id_column, str(i+1))
        row.setdefault(split_column, "unspecified")
    return rows
