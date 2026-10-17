"""Conservative regex-only PII *hints*: NOT a de-identification guarantee."""
import re

PATTERNS = {
    "email": re.compile(r"(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?![\w.-])"),
    "ipv4": re.compile(r"\b(?:25[0-5]|2[0-4]\d|1?\d?\d)(?:\.(?:25[0-5]|2[0-4]\d|1?\d?\d)){3}\b"),
    "phone_candidate": re.compile(r"(?<!\w)(?:\+?\d[\d .()-]{7,}\d)(?!\w)"),
}


def pii_spans(text):
    """Only emit offsets/types; never include sensitive matched values in a report."""
    spans = []
    for kind, pattern in PATTERNS.items():
        for match in pattern.finditer(text):
            spans.append({"type": kind, "start": match.start(), "end": match.end()})
    return sorted(spans, key=lambda p: (p["start"], -(p["end"] - p["start"])))


def redact(text):
    spans = pii_spans(text)
    if not spans:
        return text
    output, position = [], 0
    for span in spans:
        if span["start"] < position:
            continue
        output += [text[position:span["start"]], f"[REDACTED_{span['type'].upper()}]"]
        position = span["end"]
    output.append(text[position:])
    return "".join(output)
