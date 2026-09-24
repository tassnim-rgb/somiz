"""DatasetGenerator: orchestrates deterministic multi-asset simulation runs
and exports with full provenance.

Scenario catalog (SCENARIOS) defines canonical fault configurations used by
the CLI and experiments. Each entry is honest about what it exercises:
  healthy         : no faults (baseline fleet)
  bearing         : progressive bearing wear to failure (stop-on-failure)
  overheating     : motor cooling fault
  leakage         : internal recirculation (flow loss)
  impeller        : progressive impeller erosion
  blockage        : partial discharge blockage
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from simulation import FaultSpec, OperatingProfileSpec, SimulationConfig, Simulator

SCENARIOS: Dict[str, List[FaultSpec]] = {
    "healthy": [],
    "bearing": [FaultSpec("bearing", onset_s=1800, target=1.0, duration_s=9000)],
    "overheating": [FaultSpec("overheating", onset_s=3600, target=0.9, duration_s=6000)],
    "leakage": [FaultSpec("leakage", onset_s=3600, target=0.8, duration_s=9000)],
    "impeller": [FaultSpec("impeller", onset_s=3600, target=0.7, duration_s=12000)],
    "blockage": [FaultSpec("blockage", onset_s=2400, target=0.7, duration_s=6000)],
}

DEFAULT_DURATION_S = 21600.0
DEFAULT_FS_HZ = 1.0


@dataclass
class AssetRunSpec:
    """One simulated asset with an explicit scenario and configuration."""

    asset_id: str
    scenario: str                              # key into SCENARIOS (or custom faults)
    faults: Optional[List[FaultSpec]] = None   # override scenario catalog
    duration_s: float = DEFAULT_DURATION_S
    fs_hz: float = DEFAULT_FS_HZ
    seed: int = 0                              # resolved from master seed + index
    profile: Optional[OperatingProfileSpec] = None
    stop_on_failure: bool = True


@dataclass
class Manifest:
    """Provenance record for a generated dataset directory."""

    master_seed: int
    assets: List[Dict[str, Any]]
    generated_utc: str
    schema_version: str = "1.0"
    simulator_model: str = "rotating-machine-lumped-v1"

    def write(self, path: Path) -> None:
        path.write_text(json.dumps(self.__dict__, indent=2), encoding="utf-8")


class DatasetGenerator:
    """Deterministically generate a multi-asset dataset."""

    def __init__(self, master_seed: int = 42):
        self.master_seed = int(master_seed)

    # ------------------------------------------------------------------
    def generate(
        self,
        outdir: str | Path,
        assets: List[AssetRunSpec],
        formats: tuple = ("csv", "parquet"),
        drop_scenario_duplicates: bool = True,
    ) -> Manifest:
        out = Path(outdir)
        out.mkdir(parents=True, exist_ok=True)
        entries: List[Dict[str, Any]] = []
        seen: set = set()

        for i, spec in enumerate(assets):
            seed = self.master_seed + i * 7919
            cfg = self._config_for(spec, seed)
            frame = Simulator(cfg).run()

            base = f"{spec.asset_id}__{spec.scenario}"
            if drop_scenario_duplicates:
                key = (spec.asset_id, spec.scenario)
                if key in seen:
                    continue
                seen.add(key)

            paths = {}
            for fmt in formats:
                p = out / f"{base}.{fmt}"
                if fmt == "csv":
                    frame.to_csv(p)
                elif fmt == "parquet":
                    frame.to_parquet(p)
                else:
                    raise ValueError(f"unsupported format {fmt!r}")
                paths[fmt] = p.name

            sha = sha256_of(out / paths[formats[0]])
            entries.append({
                "asset_id": spec.asset_id,
                "scenario": spec.scenario,
                "seed": seed,
                "n_samples": frame.n_samples,
                "files": paths,
                "sha256": sha,
                "config": cfg.to_dict(),
            })

        manifest = Manifest(
            master_seed=self.master_seed,
            assets=entries,
            generated_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        )
        manifest.write(out / "manifest.json")
        return manifest

    # ------------------------------------------------------------------
    def _config_for(self, spec: AssetRunSpec, seed: int) -> SimulationConfig:
        if spec.scenario not in SCENARIOS:
            raise ValueError(
                f"unknown scenario {spec.scenario!r}; choose from {sorted(SCENARIOS)}")
        faults = list(spec.faults) if spec.faults is not None else list(SCENARIOS[spec.scenario])
        profile = spec.profile or OperatingProfileSpec(
            segments=[(spec.duration_s, 0.9)], cycle=True)
        return SimulationConfig(
            seed=seed,
            duration_s=spec.duration_s,
            fs_hz=spec.fs_hz,
            dt_phys=0.25,
            profile=profile,
            faults=faults,
            stop_on_failure=spec.stop_on_failure,
        )


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def default_fleet(master_seed: int = 42, n_per_scenario: int = 2,
                  duration_s: float = DEFAULT_DURATION_S,
                  fs_hz: float = DEFAULT_FS_HZ) -> List[AssetRunSpec]:
    """Convenience fleet: n healthy assets + n per each fault scenario."""
    assets: List[AssetRunSpec] = []
    scenarios = list(SCENARIOS)
    idx = 0
    for scenario in ["healthy", *[s for s in scenarios if s != "healthy"]]:
        for k in range(n_per_scenario):
            assets.append(AssetRunSpec(
                asset_id=f"A{idx:02d}",
                scenario=scenario,
                seed=idx,
                duration_s=duration_s,
                fs_hz=fs_hz,
            ))
            idx += 1
    return assets