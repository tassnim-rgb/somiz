import { useEffect, useState } from 'react'
import { api } from '../api'
import type {
  AnomalyRow,
  AssetSummary,
  DiagnosisRow,
  ExperimentRow,
  PredictionRow,
} from '../types'
import { Chart } from '../components/Chart'

interface FleetState {
  predictions: PredictionRow[]
  diagnoses: DiagnosisRow[]
  anomalies: AnomalyRow[]
}

export function Analytics() {
  const [assets, setAssets] = useState<AssetSummary[]>([])
  const [state, setState] = useState<Record<string, FleetState>>({})
  const [experiments, setExperiments] = useState<ExperimentRow[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let live = true
    ;(async () => {
      try {
        const list = await api.assets()
        const byId: Record<string, FleetState> = {}
        for (const a of list) {
          const [preds, diag, anom] = await Promise.all([
            api.predictions(a.asset_id, 5000),
            api.diagnoses(a.asset_id, 5000),
            api.anomalies(a.asset_id, 5000),
          ])
          byId[a.asset_id] = { predictions: preds, diagnoses: diag, anomalies: anom }
        }
        const exp = await api.experiments()
        if (!live) return
        setAssets(list)
        setState(byId)
        setExperiments(exp)
      } catch (e) {
        if (live) setError(String(e))
      }
    })()
    return () => {
      live = false
    }
  }, [])

  const faultCounts = new Map<string, number>()
  for (const s of Object.values(state)) {
    for (const d of s.diagnoses) {
      if (d.fault_type === 'healthy') continue
      faultCounts.set(d.fault_type, (faultCounts.get(d.fault_type) ?? 0) + 1)
    }
  }

  const anomalyRate = assets.map((a) => {
    const rows = state[a.asset_id]?.anomalies ?? []
    const detected = rows.filter((r) => r.is_detected).length
    const fa = rows.filter((r) => r.false_alarm_flag).length
    return {
      asset_id: a.asset_id,
      detected,
      falseAlarms: fa,
      total: rows.length,
    }
  })

  return (
    <section className="page">
      <h1>Analyse</h1>
      <p className="muted">
        Agrégats calculés sur la base SIMULÉE. Les libellés de défaut proviennent
        de la vérité simulée (ground_truth_seed) ou des modèles Phase 5.
      </p>
      {error ? <p className="error">{error}</p> : null}

      <div className="grid two">
        <div className="card">
          <h2>Comptage des défauts (vérité simulée)</h2>
          <Chart
            data={[
              {
                x: [...faultCounts.keys()],
                y: [...faultCounts.values()],
                type: 'bar',
                marker: { color: '#c62828' },
              },
            ]}
            layout={{ xaxis: { title: 'Type de défaut' }, yaxis: { title: 'Échantillons' } }}
          />
        </div>

        <div className="card">
          <h2>Anomalies détectées par actif</h2>
          <Chart
            data={[
              {
                x: anomalyRate.map((a) => a.asset_id),
                y: anomalyRate.map((a) => a.detected),
                name: 'Détectées',
                type: 'bar',
                marker: { color: '#7cb342' },
              },
              {
                x: anomalyRate.map((a) => a.asset_id),
                y: anomalyRate.map((a) => a.falseAlarms),
                name: 'Fausses alertes',
                type: 'bar',
                marker: { color: '#f9a825' },
              },
            ]}
            layout={{ barmode: 'group', yaxis: { title: 'Comptage' } }}
          />
        </div>

        <div className="card">
          <h2>Indice de santé par actif</h2>
          <Chart
            data={assets.map((a) => ({
              x: (state[a.asset_id]?.predictions ?? []).map((p) => p.ts),
              y: (state[a.asset_id]?.predictions ?? []).map((p) => p.health_index),
              name: a.asset_id,
              type: 'scatter',
              mode: 'lines',
            }))}
            layout={{ yaxis: { range: [0, 110], title: 'Indice (0-100)' }, xaxis: { title: 'Temps (s)' } }}
          />
        </div>

        <div className="card">
          <h2>Catalogue des expériences</h2>
          <table>
            <thead>
              <tr>
                <th>Expérience</th>
                <th>Résultats (fichier)</th>
              </tr>
            </thead>
            <tbody>
              {experiments.map((e) => (
                <tr key={e.id}>
                  <td>{e.name}</td>
                  <td className="muted">{String(e.metrics_json.results_file ?? '-')}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  )
}