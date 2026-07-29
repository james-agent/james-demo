"""Idiom gate: operator-facing Q2 copy must be English (en)."""

from __future__ import annotations

import re
from pathlib import Path

from ext.q2.errors import classify_http_error
from ext.q2.idiom import LOCALE, MSG_MISSING_HELIX_ENV, MSG_PROVISION_RUN_NOT_FOUND

PT_HINT = re.compile(
    r"\b(não|sim|erro|cliente|conta|provisão|sucesso|falha|pendente|configuração)\b",
    re.I,
)
ACCENTED = re.compile(r"[àáâãäåçèéêëìíîïñòóôõöùúûüýÿÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝ]")


def test_locale_is_english() -> None:
    assert LOCALE == "en"
    assert "Missing required" in MSG_MISSING_HELIX_ENV
    assert MSG_PROVISION_RUN_NOT_FOUND == "Provision run not found"


def test_error_messages_are_english() -> None:
    samples = [
        classify_http_error(401, "").message,
        classify_http_error(403, "").message,
        classify_http_error(404, "").message,
        classify_http_error(409, "").message,
        classify_http_error(500, "").message,
        MSG_MISSING_HELIX_ENV,
    ]
    for message in samples:
        assert not PT_HINT.search(message)
        assert not ACCENTED.search(message)


def test_q2_package_sources_have_no_portuguese_copy() -> None:
    root = Path(__file__).resolve().parents[1] / "ext" / "q2"
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not PT_HINT.search(text), f"Portuguese hint in {path}"
        assert not ACCENTED.search(text), f"Accented non-English copy in {path}"
