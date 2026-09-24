#!/usr/bin/env python
"""Generate a reproducible SIMULATED dataset from the digital twin.

Usage:
  python scripts/generate_dataset.py --seed 42 --outdir data/generated \
      --assets 12 --format csv,parquet --scenario bearing

Writes per-asset files plus manifest.json (provenance: seed, scenario,
config, file hashes). Nothing here is real plant data.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dataengine import AssetRunSpec, DatasetGenerator, SCENARIOS, default_fleet  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--outdir", default="data/generated")
    ap.add_argument("--assets", type=int, default=4,
                    help="fleet size: healthy + each fault scenario")
    ap.add_argument("--scenario", default=None,
                    help="single scenario to generate (default: all)")
    ap.add_argument("--format", default="csv,parquet")
    ap.add_argument("--duration", type=float, default=21600.0)
    ap.add_argument("--fs", type=float, default=1.0)
    args = ap.parse_args()

    if args.scenario:
        if args.scenario not in SCENARIOS:
            print(f"unknown scenario {args.scenario!r}; choose {sorted(SCENARIOS)}", file=sys.stderr)
            return 2
        assets = [AssetRunSpec(asset_id=f"{args.scenario}-{i:02d}",
                               scenario=args.scenario,
                               duration_s=args.duration, fs_hz=args.fs)
                  for i in range(max(1, args.assets))]
    else:
        assets = default_fleet(args.seed, n_per_scenario=max(1, args.assets),
                               duration_s=args.duration, fs_hz=args.fs)

    gen = DatasetGenerator(master_seed=args.seed)
    manifest = gen.generate(args.outdir, assets, formats=tuple(args.format.split(",")))

    print(f"generated {len(manifest.assets)} assets -> {args.outdir}")
    for a in manifest.assets:
        print(f"  {a['asset_id']:>12s} {a['scenario']:11s} "
              f"{a['n_samples']:>6d} samples seed={a['seed']} sha={a['sha256'][:12]}")
    print("manifest:", Path(args.outdir) / "manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())