// Thin typed client for the SIMULATED backend (docs/API.md).
// Calls are same-origin: vite dev proxies /api to http://127.0.0.1:8000.

import type {
  AnomalyRow,
  AssetDetail,
  AssetSummary,
  DiagnosisRow,
  ExperimentRow,
  MaintenanceEventRow,
  MaintenancePlanRow,
  MeasurementsResponse,
  PredictionRow,
  SensorInfo,
  SimulateResponse,
} from './types'

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) {
    throw new Error(`API ${res.status} pour ${path}`)
  }
  return res.json() as Promise<T>
}

async function postJSON<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    throw new Error(`API ${res.status} pour ${path}`)
  }
  return res.json() as Promise<T>
}

export const api = {
  assets: () => getJSON<AssetSummary[]>('/api/assets'),
  asset: (id: string) => getJSON<AssetDetail>(`/api/assets/${id}`),
  sensors: (id: string) => getJSON<SensorInfo[]>(`/api/assets/${id}/sensors`),
  measurements: (id: string, tag?: string, limit = 1000) => {
    const q = new URLSearchParams({ limit: String(limit) })
    if (tag) q.set('tag', tag)
    return getJSON<MeasurementsResponse>(`/api/assets/${id}/measurements?${q}`)
  },
  diagnoses: (id: string, limit = 2000) =>
    getJSON<DiagnosisRow[]>(`/api/assets/${id}/diagnoses?limit=${limit}`),
  predictions: (id: string, limit = 2000) =>
    getJSON<PredictionRow[]>(`/api/assets/${id}/predictions?limit=${limit}`),
  anomalies: (id: string, limit = 2000) =>
    getJSON<AnomalyRow[]>(`/api/assets/${id}/anomalies?limit=${limit}`),
  plans: (latest = true) =>
    getJSON<MaintenancePlanRow[]>(`/api/maintenance/plans?latest=${latest}`),
  events: () => getJSON<MaintenanceEventRow[]>('/api/maintenance/events'),
  experiments: () => getJSON<ExperimentRow[]>('/api/experiments'),
  simulate: (body: { scenario: string; seed: number; duration_s: number }) =>
    postJSON<SimulateResponse>('/api/simulate', body),
}