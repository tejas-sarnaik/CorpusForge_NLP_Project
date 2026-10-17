"""Command-line interface."""
import argparse
import csv
import json
import sys
from pathlib import Path
from .audit import AuditConfig, audit_rows
from .io import read_rows
from .privacy import redact
from .report import save_html, save_json


def build_parser():
    parser = argparse.ArgumentParser(prog="corpusforge", description="Audit NLP datasets locally")
    parser.add_argument("--version", action="version", version="CorpusForge 0.1.0")
    commands = parser.add_subparsers(dest="command", required=True)
    audit = commands.add_parser("audit", help="Generate a JSON + offline HTML report")
    audit.add_argument("--input", required=True, help="CSV or JSONL input")
    audit.add_argument("--out", default="audit_output", help="Output directory")
    audit.add_argument("--text-column", default="text")
    audit.add_argument("--split-column", default="split")
    audit.add_argument("--id-column", default="id")
    audit.add_argument("--threshold", type=float, default=0.85)
    audit.add_argument("--min-chars", type=int, default=15)
    audit.add_argument("--max-chars", type=int, default=10000)
    audit.add_argument("--ngram", type=int, default=3)
    audit.add_argument("--fail-on-leakage", action="store_true", help="Exit 2 when leakage is found")
    clean = commands.add_parser("redact", help="Write a separate CSV/JSONL with heuristic masking")
    clean.add_argument("--input", required=True)
    clean.add_argument("--output", required=True)
    clean.add_argument("--text-column", default="text")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "audit":
            cfg = AuditConfig(args.text_column, args.split_column, args.id_column,
                              args.threshold, args.min_chars, args.max_chars, args.ngram)
            rows = read_rows(args.input, args.text_column, args.split_column, args.id_column)
            report = audit_rows(rows, cfg)
            destination = Path(args.out)
            destination.mkdir(parents=True, exist_ok=True)
            save_json(report, destination / "report.json")
            save_html(report, destination / "report.html")
            print(json.dumps(report["summary"], indent=2))
            print(f"Reports: {destination / 'report.json'} and {destination / 'report.html'}")
            return 2 if args.fail_on_leakage and report["cross_split_leakage"] else 0
        if args.command == "redact":
            source = Path(args.input)
            target = Path(args.output)
            if source.resolve() == target.resolve():
                raise ValueError("Output must differ from input; original datasets are never overwritten")
            rows = read_rows(source, args.text_column)
            for row in rows:
                row[args.text_column] = redact(row[args.text_column])
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.suffix.lower() == ".csv":
                keys = list(dict.fromkeys(key for row in rows for key in row))
                with target.open("w", newline="", encoding="utf-8") as handle:
                    writer = csv.DictWriter(handle, fieldnames=keys)
                    writer.writeheader()
                    writer.writerows(rows)
            elif target.suffix.lower() in {".jsonl", ".ndjson"}:
                with target.open("w", encoding="utf-8") as handle:
                    for row in rows:
                        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
            else:
                raise ValueError("Output must have extension .csv, .jsonl or .ndjson")
            print(f"Heuristically redacted dataset written to {target}")
            return 0
    except (ValueError, OSError, KeyError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
