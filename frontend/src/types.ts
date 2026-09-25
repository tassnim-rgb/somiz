// Types mirroring the SIMULATED FastAPI backend schemas (docs/API.md).

export interface Health {
  status: string
  db: string
  version: string
}

export interface AssetSummary {
  id: number
  asset_id: string
  asset_type: string
  name: string
}

export interface AssetDetail extends AssetSummary {
  description: string | null
  params_json: Record<string, unknown>
  criticality_json: Record<string, unknown>
  created_at: string
}

export interface Criticality {
  asset_id: string
  rul_p50_days: number
  p_fail_by_horizon: number
  failure_cost: number
  maintenance_cost: number
  risk: number
  class: string
  explanation?: string
}

export interface SensorInfo {
  id: number
  tag: string
  name: string
  unit: string | null
  kind: string
}

export interface MeasurementRow {
  ts: number
  tag: string
  value: number | null
  quality_flag: string
}

export interface MeasurementsResponse {
  asset_id: string
  total: number
  rows: MeasurementRow[]
}

export interface DiagnosisRow {
  id: number
  ts: number
  fault_type: string
  probability: number | null
  severity_estimate: number | null
  affected_signals_json: Record<string, unknown>
  method: string
  model_version: string
}

export interface PredictionRow {
  id: number
  ts: number
  health_index: number | null
  rul_estimate: number | null
  rul_lower: number | null
  rul_upper: number | null
  confidence: number | null
  model_version: string
}

export interface AnomalyRow {
  id: number
  ts: number
  score: number | null
  threshold: number | null
  is_detected: boolean
  true_onset_ts: number | null
  detection_delay: number | null
  false_alarm_flag: boolean
}

export interface MaintenanceEventRow {
  id: number
  asset_id: string
  scheduled_at: string | null
  performed_at: string | null
  action_type: string
  cost: number | null
  duration_h: number | null
  outcome: string | null
}

export interface MaintenancePlanRow {
  id: number
  generated_at: string
  horizon_days: number
  objective_value: number | null
  solver: string
  plan_json: Record<string, number | null>
  constraints_json: Record<string, unknown>
}

export interface ExperimentRow {
  id: number
  name: string
  config_json: Record<string, unknown>
  metrics_json: Record<string, unknown>
  artifacts_json: Record<string, unknown>
  created_at: string
}

export interface SimulateResponse {
  simulated: true
  scenario: string
  seed: number
  duration_s: number
  n_samples: number
  stride: number
  warmup_s: number
  t: number[]
  vib: number[]
  t_motor: number[]
  p_disch: number[]
  flow: number[]
  health_index: (number | null)[]
  fault_severity: number[]
  dominant_fault: string[]
}

// Health bands are the Phase 4 a-priori scale (docs/HEALTH_INDEX.md).
export interface Band {
  key: 'NORMAL' | 'EARLY' | 'MODERATE' | 'SEVERE' | 'FAILURE'
  from: number
  to: number
  labelFr: string
  color: string
}

export const HEALTH_BANDS: Band[] = [
  { key: 'NORMAL', from: 80, to: 100, labelFr: 'Normal', color: '#2e7d32' },
  { key: 'EARLY', from: 60, to: 80, labelFr: 'Dégradation précoce', color: '#7cb342' },
  { key: 'MODERATE', from: 40, to: 60, labelFr: 'Modéré', color: '#f9a825' },
  { key: 'SEVERE', from: 20, to: 40, labelFr: 'Sévère', color: '#ef6c00' },
  { key: 'FAILURE', from: 0, to: 20, labelFr: 'Défaillance', color: '#c62828' },
]

export function bandOf(hi: number | null): Band | null {
  if (hi === null || Number.isNaN(hi)) return null
  for (const b of HEALTH_BANDS) {
    if (hi >= b.from && hi <= b.to) return b
  }
  return null
}