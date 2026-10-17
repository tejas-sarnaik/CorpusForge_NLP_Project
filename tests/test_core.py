import json
from corpusforge.audit import AuditConfig, audit_rows
from corpusforge.cli import main
from corpusforge.privacy import pii_spans, redact
from corpusforge.text import duplicate_pairs, normalize


def test_unicode_normalization():
    assert normalize("  Ｈｅｌｌｏ\nWORLD  ") == "hello world"


def test_exact_duplicates_and_cross_split_leakage():
    rows = [{"id": "a", "split": "train", "text": "Example sentence one."},
            {"id": "b", "split": "test", "text": "  EXAMPLE sentence one. "}]
    report = audit_rows(rows)
    assert report["summary"]["duplicate_pairs"] == 1
    assert report["summary"]["cross_split_leakage_pairs"] == 1
    assert report["duplicate_pairs"][0]["kind"] == "exact"


def test_near_duplicate_confirmation():
    pairs = duplicate_pairs(["the small brown dog is running today", "the small brown dog is running today"], 0.9)
    assert len(pairs) == 1


def test_pii_does_not_expose_matched_value_in_report():
    email = "someone@example.com"
    rows = [{"text": "Contact " + email, "split": "train"}]
    report = audit_rows(rows)
    assert report["rows"][0]["pii_types"] == ["email"]
    assert email not in json.dumps(report)
    assert "[REDACTED_EMAIL]" in redact(rows[0]["text"])
    assert pii_spans(rows[0]["text"])


def test_empty_dataset():
    assert audit_rows([])["summary"]["total_rows"] == 0


def test_cli_audit_end_to_end(tmp_path):
    data = tmp_path / "data.jsonl"
    data.write_text('{"id":"a","split":"train","text":"Same training sample"}\n'
                    '{"id":"b","split":"test","text":"Same training sample"}\n')
    out = tmp_path / "reports"
    assert main(["audit", "--input", str(data), "--out", str(out), "--fail-on-leakage"]) == 2
    assert (out / "report.html").exists()
    report = json.loads((out / "report.json").read_text())
    assert report["summary"]["cross_split_leakage_pairs"] == 1


def test_cli_redact_never_overwrites_original(tmp_path):
    data = tmp_path / "input.csv"
    data.write_text("text,split\nhello@example.com,train\n")
    assert main(["redact", "--input", str(data), "--output", str(data)]) == 1
    output = tmp_path / "redacted.csv"
    assert main(["redact", "--input", str(data), "--output", str(output)]) == 0
    assert "[REDACTED_EMAIL]" in output.read_text()
    assert "hello@example.com" in data.read_text()


def test_bad_threshold():
    try:
        audit_rows([{"text": "a"}], AuditConfig(similarity_threshold=2))
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid threshold error")
