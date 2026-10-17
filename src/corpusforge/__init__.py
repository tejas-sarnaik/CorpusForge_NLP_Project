"""CorpusForge: local-first text dataset auditing."""
from .audit import audit_rows, AuditConfig
from .io import read_rows
__version__ = "0.1.0"
__all__ = ["audit_rows", "AuditConfig", "read_rows"]
