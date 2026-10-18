<div align="center">

# 🔎 CorpusForge
### Know your NLP dataset *before* you train.
**A zero-runtime-dependency, local-first dataset auditor for duplicate text, train/test leakage, possible PII and text-quality anomalies.**

[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions)](.github/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Contributions welcome](https://img.shields.io/badge/Contributions-welcome-orange.svg)](CONTRIBUTING.md)

[Quick start](#-quick-start) · [Features](#-features) · [CLI](#-command-line-interface) · [Python API](#-python-api) · [Limitations](#-limitations--responsible-use) · [Contributing](CONTRIBUTING.md)
</div>

---

## 🚀 Why CorpusForge?

Training on noisy corpora or evaluating against contaminated splits can mislead NLP research. CorpusForge makes dataset issues **visible and reviewable** before you fine-tune an LLM, train a classifier, publish benchmarks, or release community datasets. It runs locally, and it does not upload your corpus to a remote service.

> **What makes this useful?** It combines split-aware near-duplicate diagnostics, transparent text-quality flags and conservative privacy indicators into **one reproducible CLI and offline HTML report**. No GPU, API keys, hosted infrastructure or ML model downloads required.

## ✨ Features

| Capability | How it works | Output |
|---|---|---|
| Exact duplicates | NFKC + casefold + whitespace normalization | Duplicate pairs |
| Near duplicates | Deterministic MinHash-LSH candidates, verified with character-shingle Jaccard | Scores + pairs |
| Data leakage | Duplicate pairs spanning named train/validation/test splits | Potential leakage pairs |
| PII hints | Conservative regex indicators for emails, IPv4 and phone candidates | Type-only flags |
| Text-quality checks | Empty, short, and long samples | Per-record issues |
| Offline reporting | Standalone HTML + machine-readable JSON | Shareable audit artifacts |
| Explicit masking | Redact detected patterns into a **new** CSV/JSONL file | Separate masked corpus |
| Automation-ready | Non-zero exit status on potential leakage | CI gates |

## ⚡ Quick start

Requirements: **Python 3.10+**. No mandatory third-party runtime packages.

```bash
git clone https://github.com/YOUR_USERNAME/CorpusForge.git
cd CorpusForge
python -m pip install -e .

# Run a sample audit
corpusforge audit --input examples/demo.jsonl --out audit_output

# View offline HTML in your browser:
# audit_output/report.html
# Inspect full machine-readable results:
# audit_output/report.json
```

Replace `YOUR_USERNAME` with the repository owner after publication. Alternatively, run without installation using `PYTHONPATH=src python -m corpusforge audit --input examples/demo.jsonl`.

### Example terminal summary

```json
{
  "total_rows": 5,
  "splits": {"train": 3, "test": 1, "validation": 1},
  "flag_counts": {"possible_pii": 1, "too_short": 1},
  "duplicate_pairs": 1,
  "cross_split_leakage_pairs": 1
}
```

### The report

The standalone `report.html` includes overview cards and per-row diagnostics. `report.json` also includes exact/near-duplicate pair metadata, similarity scores, and split-specific leakage pairs. **Raw text and detected sensitive substrings are not embedded in either report**; however, original record IDs are retained.

## 🧰 Command-line interface

```bash
# Custom CSV schemas
corpusforge audit --input my_data.csv --text-column body --split-column partition --id-column uid --out reports

# Adjust near-duplicate threshold and short-text cutoff
corpusforge audit --input examples/demo.jsonl --threshold 0.9 --min-chars 25

# Make CI fail (exit code 2) if cross-split duplicates are found
corpusforge audit --input examples/demo.jsonl --fail-on-leakage

# Write a new, heuristic-masked dataset; original remains unchanged
corpusforge redact --input examples/demo.jsonl --output masked.jsonl

corpusforge --help
```

Supported input formats: `.csv`, `.jsonl`, `.ndjson` in UTF-8. By default, use `text` for content, `id` for record IDs and `split` for split labels. Missing IDs are generated; missing splits are labeled `unspecified`. Non-string text values raise a clear error. Treat source content as untrusted.

## 🐍 Python API

```python
from corpusforge import AuditConfig, audit_rows, read_rows

rows = read_rows("examples/demo.jsonl")
report = audit_rows(rows, AuditConfig(similarity_threshold=0.85, min_chars=15))

print(report["summary"])
for pair in report["cross_split_leakage"]:
    print(pair["left_id"], pair["right_id"], pair["similarity"])
```

## 🗂 Repository layout

```text
CorpusForge/
├── src/corpusforge/
│   ├── __init__.py         # Public API
│   ├── __main__.py         # python -m corpusforge
│   ├── audit.py             # Auditing engine
│   ├── cli.py               # Audit and redact subcommands
│   ├── io.py                # CSV/JSONL schema handling
│   ├── privacy.py           # PII signals and masking
│   ├── report.py            # JSON + standalone HTML output
│   └── text.py              # Normalization, LSH + Jaccard
├── examples/demo.jsonl     # Safe synthetic sample data
├── tests/test_core.py      # Automated tests
├── docs/ARCHITECTURE.md    # Algorithms, assumptions and complexity
├── .github/                # CI and community templates
├── CONTRIBUTING.md
├── SECURITY.md
├── LICENSE                 # MIT — Tejas Sarnaik, 2026
├── pyproject.toml
└── README.md
```

## 🧪 Development and testing

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
ruff check src tests
```

CI runs on Python 3.10–3.13 for every push and pull request.

## ⚠️ Limitations & responsible use

- **Not semantic deduplication:** character-shingle Jaccard measures lexical overlap, not paraphrase meaning.
- **Not exhaustive:** MinHash-LSH candidate selection can miss near-duplicate pairs; very small edits and scripts without spaces merit careful threshold validation.
- **Not robust de-identification:** regex PII hints miss many identifiers and may wrongly mark innocent strings. Never rely on the `redact` command alone to anonymize regulated or sensitive material.
- **Not a data-cleaning autopilot:** the audit intentionally produces evidence, rather than dropping records or merging splits without review.
- **Report privacy:** audit reports avoid raw text, but IDs may be sensitive; use pseudonymous IDs if needed.
- **Scale:** in highly repetitive datasets, LSH collision counts can grow quadratically; consult the [architecture notes](docs/ARCHITECTURE.md).

## 🛣 Roadmap (proposed, not yet implemented)

- [ ] Optional embedding-based semantic duplicates
- [ ] Multi-lingual PII recognizers and configurable rules
- [ ] Streaming audit support for large Parquet datasets
- [ ] Automated dataset cards and richer interactive diagnostics
- [ ] Better calibration/evaluation benchmarks for duplicate recall
- [ ] Reusable GitHub Action and Hugging Face `datasets` adapter

Want to contribute? Pick an issue, propose a small reproducible improvement and open a PR.

## 💬 Community

Use GitHub Issues to report bugs, propose features and request documentation. Discord moderators and NLP community maintainers may share the tool, but this project does not claim an official Discord integration. See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## 📄 License

This project is licensed under the [MIT License](LICENSE).

## 🛠 Issues and Contributions

Bug reports, feature requests, and suggestions are welcome. Please open an issue in the GitHub repository.

## 📮 Contact

Questions or issues? File an issue or contact [Tejas Sarnaik](mailto:tejassarnaik2120@gmail.com).

---

© 2026 Tejas Sarnaik. All rights reserved.
