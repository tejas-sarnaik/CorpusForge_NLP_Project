"""Structured dataset audit with transparent, adjustable heuristics."""
from collections import Counter
from dataclasses import dataclass
from .privacy import pii_spans
from .text import duplicate_pairs, normalize


@dataclass(frozen=True)
class AuditConfig:
    text_column: str = "text"
    split_column: str = "split"
    id_column: str = "id"
    similarity_threshold: float = 0.85
    min_chars: int = 15
    max_chars: int = 10000
    ngram: int = 3


def audit_rows(rows, config=None):
    config = config or AuditConfig()
    if config.min_chars < 0 or config.max_chars < config.min_chars:
        raise ValueError("Invalid character length limits")
    if config.ngram < 1:
        raise ValueError("ngram must be >= 1")
    texts = [row[config.text_column] for row in rows]
    pairs = duplicate_pairs(texts, config.similarity_threshold, config.ngram)
    identifiers = [str(row.get(config.id_column, i+1)) for i, row in enumerate(rows)]
    splits = [str(row.get(config.split_column, "unspecified")) for row in rows]
    details = []
    issues = Counter()
    for index, text in enumerate(texts):
        types = sorted({x["type"] for x in pii_spans(text)})
        flags = []
        if not normalize(text):
            flags.append("empty")
        elif len(text.strip()) < config.min_chars:
            flags.append("too_short")
        if len(text) > config.max_chars:
            flags.append("too_long")
        if types:
            flags.append("possible_pii")
        issues.update(flags)
        details.append({"index": index, "id": identifiers[index], "split": splits[index],
                        "characters": len(text), "flags": flags, "pii_types": types})
    duplicates = []
    leakage = []
    for pair in pairs:
        i, j = pair["left_index"], pair["right_index"]
        item = {**pair, "left_id": identifiers[i], "right_id": identifiers[j],
                "left_split": splits[i], "right_split": splits[j]}
        duplicates.append(item)
        if splits[i] != splits[j] and "unspecified" not in (splits[i], splits[j]):
            leakage.append(item)
    return {
        "tool": "CorpusForge", "schema_version": "1.0", "configuration": vars(config),
        "summary": {"total_rows": len(rows), "splits": dict(Counter(splits)),
                    "flag_counts": dict(issues), "duplicate_pairs": len(duplicates),
                    "cross_split_leakage_pairs": len(leakage)},
        "rows": details, "duplicate_pairs": duplicates, "cross_split_leakage": leakage,
        "limitations": ["PII detection uses incomplete heuristic patterns; it is not anonymization.",
                        "Near-duplicate detection uses approximate MinHash-LSH candidate retrieval.",
                        "Similarity is character-shingle Jaccard, not semantic equivalence."]
    }
