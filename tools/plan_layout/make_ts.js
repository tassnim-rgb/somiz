#!/usr/bin/env node
// Convert the frozen ATELIERS dump (ateliers_data.json) into the typed React
// module frontend/src/data/ateliers.ts. Byte-identical output for a given input.
//
// Chain:  PDFs → OCR → gen_layout.py → layout_data.json → (spliced into
// index.html) → dump of the ATELIERS block → ateliers_data.json → make_ts.js
//         → frontend/src/data/ateliers.ts
//
// ateliers_data.json is committed as the frozen intermediate: layout numbers
// come from gen_layout.py (deterministic), while the cosmetic simulation draws
// (_wear jitter, sensor phase/omega) are captured once at dump time.
//
// Usage:  node tools/plan_layout/make_ts.js      (from anywhere)
const fs = require('fs');
const path = require('path');

const here = __dirname;
const dataPath = path.join(here, 'ateliers_data.json');
const outPath = path.join(here, '..', '..', 'frontend', 'src', 'data', 'ateliers.ts');
const d = JSON.parse(fs.readFileSync(dataPath, 'utf8'));

const file = `// Plan-derived plant data for the SOMIZ React app — GENERATED FILE.
// Source: OCR of « PLAN D'IMPLANTATION DES MACHINES ET ÉQUIPEMENTS »
// P-01 ind. 01 (DIS · DLOG · DCA 12/05/2024, Centrale 01/04/2024).
// Positions/surfaces: APPROXIMATE (OCR readings, see tools/plan_layout/README.md).
// Status/age/dates/sensor states: SIMULATED (seeded, deterministic) — not SOMIZ data.
// Regenerate with: node tools/plan_layout/make_ts.js (byte-identical; reads
// tools/plan_layout/ateliers_data.json — the frozen dump of the ATELIERS block
// in index.html; layout numbers originate from tools/plan_layout/gen_layout.py).

export type Status = 'ok' | 'warn' | 'danger' | 'critical';

export interface Zone {
  name: string; x: number; z: number; w: number; d: number;
  color: number; area?: string;
}

export interface Sensor {
  label: string; unit: string; base: number; kind: 'vib' | 'temp' | 'rpm' | 'load';
  _mean: number; _noise: number; _phase: number; _omega: number;
  _lastEvent: number; value: number;
}

export interface Equip {
  id: string; name: string; type: string; mtype: string;
  x: number; z: number; w: number; d: number;
  status: Status; criticality: 'A' | 'B' | 'C'; age: number;
  lastMaint: string; nextMaint: string; history: string[];
  sensors: Sensor[]; _wear: number;
}

export interface Atelier {
  name: string; surface: string; w: number; d: number;
  zones: Zone[]; equipment: Equip[];
}

export const STATUS_COLORS: Record<Status, number> = ${JSON.stringify(d.STATUS_COLORS)};
export const SENSOR_SCALE: Record<Status, number> = ${JSON.stringify(d.SENSOR_SCALE)};
export const WEAR_INIT: Record<Status, number> = ${JSON.stringify(d.WEAR_INIT)};

export const ATELIERS: Atelier[] = ${JSON.stringify(d.ATELIERS, null, 1)};

// Sanity inventory (plan-derived; see tools/plan_layout/README.md)
export const PLAN_META = {
  plan: 'P-01', ind: '01',
  dates: { 'Atelier DIS': '12/05/2024', 'Atelier DLOG': '12/05/2024',
           'Atelier DCA': '12/05/2024', 'Atelier Centrale': '01/04/2024' },
  machines: { 'Atelier DIS': 29, 'Atelier DLOG': 6, 'Atelier Centrale': 57, 'Atelier DCA': 6 },
  zones: { 'Atelier DIS': 8, 'Atelier DLOG': 12, 'Atelier Centrale': 10, 'Atelier DCA': 4 },
  positions: 'approximate (OCR)',
  states: 'simulated',
} as const;
`;

fs.writeFileSync(outPath, file);
console.log('wrote', outPath, fs.statSync(outPath).size, 'bytes');
