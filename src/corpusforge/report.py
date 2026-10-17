"""Offline HTML and JSON audit reporting without third-party dependencies."""
import html
import json
from pathlib import Path


def save_json(report, path):
    Path(path).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def save_html(report, path):
    summary = report["summary"]
    cards = "".join(f'<section class="card"><small>{html.escape(key.replace("_", " ").title())}</small>'
                    f'<strong>{value}</strong></section>' for key, value in summary.items()
                    if isinstance(value, int))
    rows = "".join("<tr>" + "".join(f"<td>{html.escape(str(item[key]))}</td>"
                    for key in ("id", "split", "characters", "flags", "pii_types")) + "</tr>"
                   for item in report["rows"])
    escaped_limits = "".join(f"<li>{html.escape(x)}</li>" for x in report["limitations"])
    document = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>CorpusForge Audit</title>
<style>body{{font-family:system-ui,sans-serif;margin:2rem auto;padding:0 1rem;max-width:1100px;background:#f6f8fc;color:#172034}}
header{{background:#10213d;color:white;padding:2rem;border-radius:1rem}}h1{{margin:0}}.cards{{display:flex;flex-wrap:wrap;gap:1rem;margin:1.5rem 0}}
.card{{background:white;border:1px solid #dde4ef;border-radius:.7rem;padding:1rem;min-width:175px;display:grid;gap:.5rem}}
.card strong{{font-size:2rem;color:#173c76}}table{{border-collapse:collapse;width:100%;background:white}}th,td{{text-align:left;border-bottom:1px solid #ddd;padding:.75rem;vertical-align:top}}th{{background:#eaf0fa}}
.note{{padding:1rem;background:#fff3d7;border-radius:.5rem}}.scroll{{overflow-x:auto}}</style></head>
<body><header><h1>CorpusForge / Dataset Audit</h1><p>Local-first dataset hygiene report</p></header>
<div class="cards">{cards}</div><h2>Per-row diagnostics</h2><div class="scroll"><table><thead><tr><th>ID</th><th>Split</th><th>Characters</th><th>Flags</th><th>PII types</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Interpretation &amp; limitations</h2><div class="note"><ul>{escaped_limits}</ul></div>
<p>Detailed duplicate and leakage pairs are in the JSON report. Original text is intentionally omitted from reports.</p></body></html>"""
    Path(path).write_text(document, encoding="utf-8")
