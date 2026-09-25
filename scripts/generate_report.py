#!/usr/bin/env python
"""Generate the SOMIZ platform report (HTML + PDF) from the versioned
result artefacts (Phases 4-9). Renders reports/generated/somiz_report.{html,pdf}
using jinja2 + WeasyPrint. No value is fabricated or recomputed here: the
report is a projection of the tracked JSON results.

Usage: python scripts/generate_report.py [--outdir reports/generated]
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from jinja2 import Environment, FileSystemLoader, select_autoescape

RESULTS = ROOT / "experiments" / "results"


def load(name: str) -> dict:
    return json.loads((RESULTS / name).read_text(encoding="utf-8"))


def build_context() -> dict:
    anomaly = load("anomaly_comparison.json")
    diag = load("diagnosis_rul_comparison.json")
    opt = load("optimization_comparison.json")
    research = load("research_comparison.json")

    detectors = sorted(anomaly["detectors"], key=lambda d: -float(d["auc"]))
    stat_det = next(d for d in anomaly["detectors"] if d["method"] == "statistical")

    # normalised diagnosis table (method -> metric)
    diagnosis = []
    for m in ["gradient_boosting", "random_forest", "mlp", "heuristic"]:
        if m in diag["diagnosis"]:
            diagnosis.append((m, {"metric": diag["diagnosis"][m]["metrics"]}))
    dl = {name: d["metric"]["macro_f1"]
          for name, d in diagnosis if "heuristic" not in name}
    best_diag = max(dl.values())

    # normalised RUL pooled table
    rul = []
    mae = {"ridge": diag["rul"]["ridge"]["pooled"]["mae_s"],
           "gbm": diag["rul"]["gbm"]["pooled"]["mae_s"]}
    rul.append(("ridge (régression)", {"pooled": diag["rul"]["ridge"]["pooled"]}))
    rul.append(("gbm (arbre)", {"pooled": diag["rul"]["gbm"]["pooled"]}))
    q = diag["rul"]["quantile_gbm"]
    rul.append(("gbm quantile (médiane)", {"pooled": q["pooled_median"]}))
    mlp_per = diag["rul"]["window_mlp"]["per_scenario_mae_s"]
    rul.append(("mlp fenêtré (strictement causal)", {
        "pooled": {
            "mae_s": round(statistics.median([float(v) for v in mlp_per.values()]), 1)
            if mlp_per else "-",
            "rmse_s": "-",
            "mae_min": "-",
        }}))

    # research: exp3 pivoted per mode
    exp3p: dict = {}
    for r in research["exp3_early_detection"]["rows"]:
        exp3p.setdefault(r["scenario"], {})[int(r["onset_s"])] = r["delay_s"]
    exp3_table = [
        (scen, exp3p[scen].get(100), exp3p[scen].get(300), exp3p[scen].get(500))
        for scen in exp3p
    ]
    delays = [r["delay_s"] for r in research["exp3_early_detection"]["rows"]
              if r["delay_s"] is not None]
    exp1 = {scen: {**r,
                   "auc_twin": round(float(r["auc_twin"]), 4),
                   "auc_statistical": round(float(r["auc_statistical"]), 4),
                   "auc_hybrid": round(float(r["auc_hybrid"]), 4)}
            for scen, r in research["exp1_detector_comparison"]["per_mode"].items()}
    exp2 = [{**r, "severity_at_detection": round(r["severity_at_detection"], 3)}
            for r in research["exp2_noise_robustness"]["rows"]]

    return {
        "version": "0.1.0",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "summary": {
            "anomaly_auc": str(round(float(stat_det["auc"]), 4)),
            "diagnosis_macro_f1": f"{best_diag:.4f}",
            "heuristic_macro_f1": f"{diag['diagnosis']['heuristic']['metrics']['macro_f1']:.3f}",
            "rul_gbm_mae": f"{mae['gbm']:.1f}",
            "rul_coverage": f"{q['interval_coverage_p10_90']:.4f}",
            "rul_width": f"{q['mean_interval_width_s']:.0f}",
            "opt_saving": f"{opt['headline']['milp_vs_do_nothing_saving_pct']:.1f}",
            "opt_vs_greedy": f"{opt['headline']['milp_vs_greedy_saving_pct']:.1f}",
            "research_delay_range": f"{min(delays)}-{max(delays)} s",
        },
        "anomalies": detectors,
        "diagnosis": diagnosis,
        "rul": rul,
        "optimization": opt,
        "research": {
            "exp1": exp1,
            "exp2": exp2,
            "exp3_table": exp3_table,
            "exp4_curve": research["exp4_fa_fn_tradeoff"]["thresholds"][::5],
            "exp4_best": research["exp4_fa_fn_tradeoff"]["operating_point"],
            "exp5": research["exp5_optimisation_value"]["rows"],
        },
        "limits": [
            "Tous les capteurs, défauts, diagnostics, RUL et plans sont issus du jumeau numérique simulé (phase 2) et des modèles entraînés dessus.",
            "Aucune donnée d'un site réel ; noms et parc illustratifs.",
            "Les classes de criticité A/B/C sont des terciles de risque du parc (postulat de modèle).",
            "Le plan de maintenance optimal est optimal pour les entrées RUL/coûts simulées données, pas pour une usine réelle.",
            "La robustesse du plan aux erreurs de RUL est une piste de recherche ouverte (phase 9 n'en prétend pas la preuve).",
            "Le détecteur heuristique est conservé comme barre sans ML et mesure un plafond naïf volontairement bas.",
        ],
        "artifacts": [
            {"path": "anomaly_comparison.json", "elapsed_s": anomaly.get("elapsed_s", "-")},
            {"path": "diagnosis_rul_comparison.json", "elapsed_s": diag.get("elapsed_s", "-")},
            {"path": "optimization_comparison.json", "elapsed_s": opt.get("elapsed_s", "-")},
        ],
        "research_file": "research_comparison.json",
        "research_elapsed_s": research.get("runtime_s", "-"),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--outdir", default=str(ROOT / "reports" / "generated"))
    args = ap.parse_args(argv)

    ctx = build_context()
    env = Environment(
        loader=FileSystemLoader(str(ROOT / "reports" / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    html = env.get_template("somiz_report.html.j2").render(**ctx)

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    html_path = out / "somiz_report.html"
    html_path.write_text(html, encoding="utf-8")

    from weasyprint import HTML

    doc = HTML(string=html, base_url=str(ROOT)).render()
    pdf_path = out / "somiz_report.pdf"
    doc.write_pdf(str(pdf_path))
    pages = len(doc.pages)

    manifest = {
        "generated_at": ctx["generated_at"],
        "html": html_path.name,
        "pdf": pdf_path.name,
        "pages": pages,
        "artifacts": [a["path"] for a in ctx["artifacts"]] + [ctx["research_file"]],
        "size_html_bytes": html_path.stat().st_size,
        "size_pdf_bytes": pdf_path.stat().st_size,
    }
    (out / "report_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[report] HTML  {html_path} ({manifest['size_html_bytes']} B)")
    print(f"[report] PDF   {pdf_path} ({manifest['size_pdf_bytes']} B, "
          f"{pages} pages)")
    print(f"[report] manifest written; artefacts: {manifest['artifacts']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())