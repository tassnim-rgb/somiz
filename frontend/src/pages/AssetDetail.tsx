import { useEffect, useMemo, useState } from 'react'
import { useParams } from 'react-router-dom'
import { api } from '../api'
import type {
  DiagnosisRow,
  MaintenanceEventRow,
  MeasurementRow,
  PredictionRow,
  SensorInfo,
} from '../types'
import { Chart } from '../components/Chart'
import { HealthBadge } from '../components/HealthBadge'
import { StatChip } from '../components/StatChip'

export function AssetDetail() {
  const { id = 'A00' } = useParams()
  const [sensors, setSensors] = useState<SensorInfo[]>([])
  const [measurements, setMeasurements] = useState<MeasurementRow[]>([])
  const [predictions, setPredictions] = useState<PredictionRow[]>([])
  const [diagnoses, setDiagnoses] = useState<DiagnosisRow[]>([])
  const [events, setEvents] = useState<MaintenanceEventRow[]>([])
  const [tag, setTag] = useState<string>('vib')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let live = true
    setLoading(true)
    ;(async () => {
      try {
        const [sens, meas, preds, diag, evts] = await Promise.all([
          api.sensors(id),
          api.measurements(id, tag, 1500),
          api.predictions(id, 3000),
          api.diagnoses(id, 3000),
          api.events(),
        ])
        if (!live) return
        setSensors(sens)
        setMeasurements(meas.rows)
        setPredictions(preds)
        setDiagnoses(diag)
        setEvents(evts.filter((e) => e.asset_id === id))
      } catch (e) {
        if (live) setError(String(e))
      } finally {
        if (live) setLoading(false)
      }
    })()
    return () => {
      live = false
    }
  }, [id, tag])

  const series = useMemo(() => {
    const byTag = new Map<string, MeasurementRow[]>()
    for (const m of measurements) {
      const arr = byTag.get(m.tag) ?? []
      arr.push(m)
      byTag.set(m.tag, arr)
    }
    return byTag
  }, [measurements])

  const active = series.get(tag) ?? []
  const sensor = sensors.find((s) => s.tag === tag)
  const lastPred = predictions[predictions.length - 1]
  const lastDiag = diagnoses[diagnoses.length - 1] ?? null

  const hiTrace = {
    x: predictions.map((p) => p.ts),
    y: predictions.map((p) => p.health_index),
    name: 'Indice de santé',
    type: 'scatter',
    mode: 'lines',
    line: { color: '#1565c0' },
    connectgaps: false,
  }
  const sevTrace = {
    x: diagnoses.map((d) => d.ts),
    y: diagnoses.map((d) => d.severity_estimate ?? 0),
    name: 'Gravité (vérité simulée)',
    type: 'scatter',
    mode: 'lines',
    line: { color: '#c62828' },
    yaxis: 'y2',
  }

  return (
    <section className="page">
      <h1>Détail de l&apos;actif {id}</h1>
      <p className="muted">
        Séries temporelles et diagnostics SIMULÉS. Les diagnostics de base sont
        issus de la vérité simulée (method=ground_truth_seed).
      </p>
      {loading ? (
        <p className="muted">Chargement...</p>
      ) : error ? (
        <p className="error">{error}</p>
      ) : (
        <>
          <div className="chips">
            <StatChip label="Indice de santé" value={<HealthBadge hi={lastPred?.health_index ?? null} />} />
            <StatChip
              label="RUL estimée (s)"
              value={lastPred?.rul_estimate !== null && lastPred?.rul_estimate !== undefined
                  ? Math.round(lastPred.rul_estimate).toLocaleString('fr-FR')
                  : '-'}
              hint="Durée de vie résiduelle point estimée (données simulées)."
            />
            <StatChip
              label="Diagnostic tendance"
              value={lastDiag?.fault_type ?? '-'}
              tone={lastDiag?.fault_type !== 'healthy' ? 'warn' : 'ok'}
            />
            <StatChip label="Graphique temps réel" value={sensor ? `${sensor.name} (${sensor.unit ?? ''})` : tag} />
          </div>

          <div className="card">
            <div className="row space-between">
              <h2>Capteur : {sensor ? `${sensor.name} (${sensor.unit ?? ''})` : tag}</h2>
              <select value={tag} onChange={(e) => setTag(e.target.value)}>
                {sensors.map((s) => (
                  <option key={s.tag} value={s.tag}>
                    {s.name} ({s.unit ?? ''})
                  </option>
                ))}
              </select>
            </div>
            <Chart
              data={[
                {
                  x: active.map((m) => m.ts),
                  y: active.map((m) => m.value),
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#1565c0', width: 1.5 },
                },
              ]}
              layout={{ xaxis: { title: 'Temps (s)' }, yaxis: { title: sensor?.name ?? tag } }}
            />
            {active.some((m) => m.quality_flag === 'MISSING') ? (
              <p className="muted">Les trous dans la courbe sont des pertes de mesure simulées (flag MISSING).</p>
            ) : null}
          </div>

          <div className="card">
            <h2>Indice de santé et gravité au fil du temps</h2>
            <Chart
              data={[hiTrace, sevTrace] as unknown as Record<string, unknown>[]}
              layout={{
                yaxis: { range: [0, 110], title: 'Indice (0-100)' },
                yaxis2: { overlaying: 'y', side: 'right', title: 'Gravité', range: [0, 1.05] },
              }}
            />
          </div>

          <div className="card">
            <h2>Diagnostics SIMULÉS (échantillon)</h2>
            <table>
              <thead>
                <tr>
                  <th>Temps (s)</th>
                  <th>Défaut</th>
                  <th>Gravité estimée</th>
                  <th>Méthode</th>
                </tr>
              </thead>
              <tbody>
                {diagnoses.slice(-40).map((d) => (
                  <tr key={d.id}>
                    <td>{d.ts.toLocaleString('fr-FR')}</td>
                    <td>{d.fault_type === 'healthy' ? 'Aucun' : d.fault_type}</td>
                    <td>{d.severity_estimate?.toFixed(3)}</td>
                    <td>{d.method}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {events.length > 0 ? (
            <div className="card">
              <h2>Événements de maintenance prévus</h2>
              <table>
                <thead>
                  <tr>
                    <th>Date prévue</th>
                    <th>Action</th>
                    <th>Coût (EUR)</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((e, i) => (
                    <tr key={i}>
                      <td>{e.scheduled_at ? new Date(e.scheduled_at).toLocaleDateString('fr-FR') : '-'}</td>
                      <td>{e.action_type}</td>
                      <td>{e.cost?.toLocaleString('fr-FR')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </>
      )}
    </section>
  )
}