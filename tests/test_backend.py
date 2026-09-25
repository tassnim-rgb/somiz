"""Phase 7 API tests: endpoints, validation, honest SIMULATED labels.

Runs against a temp database seeded by scripts/seed_database.py so tests
never touch the developer's real data/somiz.db file.
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

DB_FD, DB_PATH = tempfile.mkstemp(suffix=".db")
os.close(DB_FD)
os.environ["SOMIZ_DB"] = DB_PATH


@pytest.fixture(scope="session", autouse=True)
def seeded_db():
    subprocess.run(
        [sys.executable, "scripts/seed_database.py", "--reset"],
        cwd=ROOT, check=True, capture_output=True,
    )
    yield
    try:
        os.unlink(DB_PATH)
    except OSError:
        pass


from backend.main import app  # noqa: E402  (after env/db setup)
from fastapi.testclient import TestClient  # noqa: E402

client = TestClient(app)


# ---------------------------------------------------------------------------
def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["db"] == "ok"
    assert body["version"]


def test_openapi_docs_available():
    r = client.get("/openapi.json")
    assert r.status_code == 200
    assert "/api/assets" in r.json()["paths"]


def test_list_assets():
    r = client.get("/api/assets")
    assert r.status_code == 200
    assets = r.json()
    assert len(assets) >= 4
    ids = {a["asset_id"] for a in assets}
    assert {"A00", "A01", "A02", "A03"} <= ids
    # summary has no secrets and no heavy fields
    assert set(assets[0]) == {"id", "asset_id", "asset_type", "name"}


def test_asset_detail():
    r = client.get("/api/assets/A01")
    assert r.status_code == 200
    a = r.json()
    assert a["asset_type"] == "motor-driven-centrifugal-pump"
    assert "simulated" in a["description"].lower()
    assert "criticality_json" in a


def test_asset_detail_unknown_404():
    r = client.get("/api/assets/NOPE")
    assert r.status_code == 404


def test_create_asset_and_validation():
    ok = client.post("/api/assets", json={
        "asset_id": "TEST-1",
        "asset_type": "motor-driven-centrifugal-pump",
        "name": "test pump",
        "params_json": {"scenario": "healthy"},
    })
    assert ok.status_code == 201
    assert ok.json()["asset_id"] == "TEST-1"
    # duplicate -> 409
    dup = client.post("/api/assets", json={
        "asset_id": "TEST-1",
        "asset_type": "motor-driven-centrifugal-pump",
        "name": "dupe",
    })
    assert dup.status_code == 409
    # invalid payload -> 422 (validation gate)
    bad = client.post("/api/assets", json={
        "asset_id": "b@d id!",
        "asset_type": "",
        "name": "",
    })
    assert bad.status_code == 422


def test_measurements_paging_and_tag_filter():
    r = client.get("/api/assets/A00/measurements", params={"limit": 50})
    assert r.status_code == 200
    body = r.json()
    assert body["asset_id"] == "A00"
    assert body["total"] > 1000
    assert len(body["rows"]) == 50
    assert "ts" in body["rows"][0] and "value" in body["rows"][0]
    vib = client.get("/api/assets/A00/measurements",
                     params={"tag": "vib", "limit": 5})
    assert all(row["tag"] == "vib" for row in vib.json()["rows"])


def test_sensors_endpoint():
    r = client.get("/api/assets/A00/sensors")
    assert r.status_code == 200
    tags = [s["tag"] for s in r.json()]
    assert {"vib", "t_motor", "p_disch", "flow"} <= set(tags)


def test_diagnoses_have_severity_and_honest_method():
    r = client.get("/api/assets/A01/diagnoses", params={"limit": 500})
    assert r.status_code == 200
    rows = r.json()
    assert rows
    for d in rows:
        assert d["fault_type"] in {"healthy", "bearing", "leakage",
                                   "blockage", "overheating", "impeller"}
        assert d["severity_estimate"] is not None
        assert d["method"].startswith("ground_truth_seed") or d["method"] != ""


def test_fault_label_follows_severity_threshold():
    # A01 bearing: before onset (ts < onset) the label must be "healthy"
    rows = client.get("/api/assets/A01/diagnoses", params={"limit": 500}).json()
    early = [d for d in rows if d["ts"] < 300.0]
    late = [d for d in rows if d["ts"] >= 300.0]
    assert early and late
    assert all(d["fault_type"] == "healthy" for d in early)
    assert any(d["fault_type"] == "bearing" for d in late)


def test_predictions_health_index_warmup_no_fabrication():
    rows = client.get("/api/assets/A00/predictions", params={"limit": 500}).json()
    assert rows
    # warmup: no health index before the configured warmup window
    early = [d for d in rows if d["ts"] < 120.0]
    assert all(d["health_index"] is None for d in early)
    steady = [d for d in rows if d["ts"] >= 200.0]
    assert all(d["health_index"] is not None for d in steady)


def test_anomalies_endpoint():
    r = client.get("/api/assets/A01/anomalies", params={"limit": 500})
    assert r.status_code == 200
    rows = r.json()
    assert rows
    assert all("is_detected" in d and "score" in d for d in rows)


def test_maintenance_plan_and_events():
    plans = client.get("/api/maintenance/plans", params={"latest": True}).json()
    assert len(plans) == 1
    p = plans[0]
    assert p["solver"] == "scipy-milp"
    assert isinstance(p["objective_value"], float)
    assert p["objective_value"] > 0
    events = client.get("/api/maintenance/events").json()
    assert len(events) >= 3
    for e in events:
        assert e["asset_id"] in {"A00", "A01", "A02", "A03"}
        assert e["action_type"] == "preventive"


def test_maintenance_events_per_asset():
    r = client.get("/api/assets/A01/maintenance-events")
    assert r.status_code == 200
    assert all(e["asset_id"] == "A01" for e in r.json())


def test_experiments_catalogue():
    rows = client.get("/api/experiments").json()
    names = {e["name"] for e in rows}
    assert {"phase4-anomaly", "phase5-diagnosis-rul",
            "phase6-optimization"} <= names
    assert all("results_file" in e["metrics_json"] for e in rows)


def test_measurements_bad_params_422():
    r = client.get("/api/assets/A00/measurements", params={"limit": -1})
    assert r.status_code == 422
    r = client.get("/api/assets/A00/measurements", params={"limit": 10**9})
    assert r.status_code == 422