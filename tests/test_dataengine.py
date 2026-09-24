"""Tests for the dataset generator: determinism, provenance, scenario
validation, export round-trips."""

from __future__ import annotations

import json
import pandas as pd
import pytest

from dataengine import AssetRunSpec, DatasetGenerator, SCENARIOS, default_fleet
from dataengine.generator import sha256_of


def _specs(duration=300.0, n=2) -> list:
    scenarios = ["healthy", "bearing", "leakage"]
    out = []
    for s in scenarios:
        for i in range(n):
            out.append(AssetRunSpec(asset_id=f"{s}-{i:02d}", scenario=s,
                                    duration_s=duration))
    return out


def test_generation_is_deterministic(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    gen = DatasetGenerator(master_seed=7)
    ma = gen.generate(a, _specs(), formats=("csv",))
    mb = gen.generate(b, _specs(), formats=("csv",))
    assert len(ma.assets) == len(mb.assets)
    for ea, eb in zip(ma.assets, mb.assets):
        assert ea["sha256"] == eb["sha256"]
        assert ea["seed"] == eb["seed"]


def test_generation_changes_with_master_seed(tmp_path):
    gen = DatasetGenerator(master_seed=1)
    m1 = gen.generate(tmp_path / "s1", _specs(duration=120.0, n=1), formats=("csv",))
    m2 = gen.generate(tmp_path / "s2", _specs(duration=120.0, n=1), formats=("csv",))
    gen2 = DatasetGenerator(master_seed=2)
    m3 = gen2.generate(tmp_path / "s3", _specs(duration=120.0, n=1), formats=("csv",))
    assert m1.assets[0]["sha256"] == m2.assets[0]["sha256"]
    assert m1.assets[0]["sha256"] != m3.assets[0]["sha256"]  # sensor noise differs


def test_manifest_self_describing(tmp_path):
    gen = DatasetGenerator(master_seed=3)
    man = gen.generate(tmp_path, _specs(duration=120.0, n=1), formats=("csv",))
    assert man.master_seed == 3
    a = man.assets[0]
    for key in ["asset_id", "scenario", "seed", "n_samples", "files", "sha256", "config"]:
        assert key in a
    assert (tmp_path / "manifest.json").exists()
    doc = json.loads((tmp_path / "manifest.json").read_text())
    assert doc["schema_version"] == "1.0"
    assert doc["simulator_model"] == "rotating-machine-lumped-v1"


def test_csv_export_readable_with_expected_columns(tmp_path):
    gen = DatasetGenerator(master_seed=4)
    man = gen.generate(tmp_path, _specs(duration=120.0, n=1), formats=("csv",))
    f = tmp_path / man.assets[0]["files"]["csv"]
    df = pd.read_csv(f)
    for col in ["t", "vib", "flow", "health_stage", "fault_severity", "dominant_fault"]:
        assert col in df.columns


def test_parquet_export_roundtrip(tmp_path):
    gen = DatasetGenerator(master_seed=5)
    man = gen.generate(tmp_path, _specs(duration=120.0, n=1), formats=("parquet",))
    f = tmp_path / man.assets[0]["files"]["parquet"]
    df = pd.read_parquet(f)
    assert len(df) > 100
    assert df["t"].is_monotonic_increasing


def test_unknown_scenario_rejected(tmp_path):
    gen = DatasetGenerator(master_seed=6)
    with pytest.raises(ValueError):
        gen.generate(tmp_path, [AssetRunSpec("x", "nonsense", duration_s=10)])


def test_scenario_catalogue_uses_known_faults():
    from simulation import FaultSpec
    for name, faults in SCENARIOS.items():
        assert name == "healthy" or faults, f"{name} has no faults"
        for f in faults:
            assert isinstance(f, FaultSpec)
            assert 0.0 <= f.onset_s


def test_default_fleet_structure():
    fleet = default_fleet(master_seed=1, n_per_scenario=1)
    names = {a.scenario for a in fleet}
    assert names == set(SCENARIOS)
    assert len(fleet) == len(SCENARIOS)  # 1 per scenario


def test_bearing_scenario_contains_failure_stage(tmp_path):
    from simulation import FaultSpec
    gen = DatasetGenerator(master_seed=8)
    spec = AssetRunSpec("pump-1", "bearing", duration_s=600.0,
                        faults=[FaultSpec("bearing", onset_s=100, target=1.0,
                                          duration_s=300)])
    tmp = tmp_path / "d"
    gen.generate(tmp, [spec], formats=("csv",))
    df = pd.read_csv(tmp / "pump-1__bearing.csv")
    assert "FAILURE" in set(df["health_stage"])
    # ground-truth progression recorded on the same frame
    assert (df["d_bearing"] >= 0.0).all() and (df["d_bearing"] <= 1.0).all()


def test_sha256_utility(tmp_path):
    import hashlib
    p = tmp_path / "x.bin"
    p.write_bytes(b"hello")
    assert sha256_of(p) == hashlib.sha256(b"hello").hexdigest()