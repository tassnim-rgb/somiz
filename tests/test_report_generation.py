"""Phase 9 regression tests: the report pipeline (jinja2 + WeasyPrint).

The report generator is a pure projection of the versioned result artefacts;
these tests assert that rendering succeeds, that the HTML and PDF come out,
and that the honest-label banner is present. They do not recompute any metric.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from scripts.generate_report import build_context

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def report_out(tmp_path_factory):
    """Render the report once into a temp dir."""
    out = tmp_path_factory.mktemp("somiz_report")
    from scripts.generate_report import main as generate

    outdir = str(out)
    generate(["--outdir", outdir])
    return out


def test_report_context_builds() -> None:
    ctx = build_context()
    assert ctx["summary"]["heuristic_macro_f1"].startswith("0.3")
    assert ctx["summary"]["rul_coverage"]  # measured Phase 5 coverage
    assert ctx["research"]["exp3_table"], "early-detection table must be non-empty"
    assert ctx["research"]["exp5"], "optimisation sweep must be non-empty"


def test_report_html_and_pdf_generated(report_out: Path) -> None:
    html = report_out / "somiz_report.html"
    pdf = report_out / "somiz_report.pdf"
    assert html.exists() and html.stat().st_size > 5_000
    assert pdf.exists() and pdf.stat().st_size > 10_000
    text = html.read_text(encoding="utf-8")
    assert "DONNÉES 100 % SIMULÉES" in text
    assert "Aucun site réel" in text
    assert "research_comparison.json" in text


def test_report_manifest(report_out: Path) -> None:
    manifest = json.loads((report_out / "report_manifest.json").read_text())
    assert set(manifest["artifacts"]) == {
        "anomaly_comparison.json",
        "diagnosis_rul_comparison.json",
        "optimization_comparison.json",
        "research_comparison.json",
    }
    assert manifest["pages"] >= 3


def test_report_does_not_clobber_tracked_artifacts() -> None:
    # generation writes only under reports/generated; the versioned experiment
    # results must remain byte-identical.
    before = {}
    for name in [
        "anomaly_comparison.json",
        "diagnosis_rul_comparison.json",
        "optimization_comparison.json",
        "research_comparison.json",
    ]:
        p = ROOT / "experiments" / "results" / name
        before[name] = p.read_bytes()
    tmp = ROOT / "reports" / "generated" / ".verify_tmp"
    shutil.rmtree(tmp, ignore_errors=True)
    from scripts.generate_report import main as generate

    generate(["--outdir", str(tmp)])
    for name, data in before.items():
        assert (ROOT / "experiments" / "results" / name).read_bytes() == data
    shutil.rmtree(tmp, ignore_errors=True)