# tools/plan_layout — plan-derived implantation for the legacy viewer

This folder holds the OCR + layout pipeline that produced the `ATELIERS`
block spliced into the root [`index.html`](../../index.html) (legacy 3D
plant viewer). It exists so the implantation can be **audited or regenerated**
without trusting the committed numbers.

## Source drawings

Client scans (not committed — original PDFs live outside the repo):

| File | Drawing | Title-block date |
|---|---|---|
| `ATELIER DIS (2).pdf` | Atelier DIS | 12/05/2024 |
| `ATELIER DLOG (2).pdf` | Atelier DLOG | 12/05/2024 |
| `ATELIER DCA (2).pdf` | Atelier DCA | 12/05/2024 |
| `Atelier centrale.PDF` | Atelier Centrale | 01/04/2024 |

All four are **Plan P-01, ind. 01**, « PLAN D'IMPLANTATION DES MACHINES ET
ÉQUIPEMENTS » (SOMIZ, Arzew). Each page is a scanned raster image with **no
text layer**, so every reading goes through OCR and is therefore
**approximate**.

## Pipeline

```text
PDF scans
  └─ rasterize → raw_<plan>-001-000.jpg (4960 × 3507 px, ~420 dpi)
       ├─ ocr_all.py            full-page OCR  → ocr_<plan>.json
       ├─ ocr_all.py --tiles     2×2 overlapping crops at native res
       │                        (catches small equipment tags) → ocr_<plan>_tiles.json
       ├─ ocr_pass2.py          zoom pass over label areas → ocr_pass2.json
       └─ analyze.py            zone names / printed S= areas → plan_extract.json
            └─ [manual curation] → labels_<plan>.txt   (format: y x score text)
                 └─ gen_layout.py  (pure Python 3, stdlib only)
                      ├─ ateliers_snippet.js   ← the ATELIERS block
                      ├─ layout_summary.txt    ← readable inventory
                      └─ layout_data.json      ← full machine/zone data
```

OCR stages need `pip install rapidocr-onnxruntime pillow`; the rasterized
scans must sit next to the scripts under the exact names in `PLANS`
(see `ocr_all.py`).

### React branch (dashboard data)

```text
index.html ATELIERS block (after splicing ateliers_snippet.js)
  └─ dump of the block        → ateliers_data.json   (frozen, committed)
       └─ make_ts.js           → frontend/src/data/ateliers.ts  (byte-identical)
```

`ateliers_data.json` is committed as the **frozen intermediate**: layout
numbers originate from `gen_layout.py` (deterministic), while the cosmetic
simulation draws (`_wear` jitter, sensor phase/omega) are captured once at
dump time — re-dumping would redraw those. The typed module feeds both
dashboard plan views (`/plan` 2D SVG, `/plan3d` three.js) with the same
98 machines / 34 zones as the legacy viewer.

## Calibration

- **DIS**: scale `0.02745 m/px`, from the only legible overall cote
  **91,41 m** measured on the plan outline (pixel rect x 490–3820,
  y 200–2180) → 91.41 × 54.35 m footprint.
- **DLOG** `0.019`, **DCA** `0.0204`, **Centrale** `0.022 m/px`: estimated
  from the printed `S=` surfaces (no legible overall cote at scan
  resolution). Treat all positions as **approximate**, not survey data.

## How `gen_layout.py` works

1. **Labels** are read per plan and clustered into blocks (union-find,
   dx ≤ 90, dy ≤ 50 px) so multi-line names (`Presse` + `Électrique`) stay
   one machine, then matched against a per-plan spec table
   `M(key, anchor, name, mtype, typ)` — full-pattern anchors first, first-word
   keys as fallback, longest match wins.
2. **Dedupe** drops repeated readings: accent/space-insensitive equality,
   substring containment at the same spot, or `difflib` ratio ≥ 0.6 for
   co-located variants (`Tronconneuse` / `Trongonneuse`).
3. **Zones**: hall rectangles are hand-traced from the scan and clamped to
   the building; rooms are auto-placed by a 60 × 60 grid search that keeps
   the plan's printed size whenever the room stays within
   `max(size, 5 m) × 1.3` of its label anchor, shrinking only when blocked
   (and finally falling back to the globally nearest free rect).
4. **Machines** are pushed apart until overlap-free and clamped inside the
   footprint.
5. **States are simulated**, deterministically: a per-id seed
   (`sum(ord(c)*(i+3)) ^ 0x5EED`) picks status (ok .66 / warn .17 /
   danger .10 / critical .07), age, maintenance dates and history lines.

Regenerating must reproduce `ateliers_snippet.js` **byte-for-byte**:

```bash
python3 gen_layout.py    # outputs land next to the script
```

Then splice: replace the `const ATELIERS = [ … ];` block in `index.html`
with `ateliers_snippet.js`, and check the page script with `node --check`.

## Expected inventory (sanity check)

**98 machines, 34 zones** — DIS 29 / DLOG 6 / Centrale 57 / DCA 6, plus
zones: DIS 8, DLOG 12, Centrale 10, DCA 4. `layout_summary.txt` lists them
with the OCR source string for each machine; anything unmatched shows up
under `unused word-labels` and should only be zone titles or dimensions.

## Honesty rules (do not relax)

- Positions and surfaces are **approximate OCR readings**, labelled as such
  in the UI (topbar chip, sidebar source note, grid label, panel footnote).
- Health states, ages, and maintenance histories are **SIMULATED** — never
  presented as SOMIZ maintenance data.
- Never claim this is deployed at SOMIZ or exported from their systems.
