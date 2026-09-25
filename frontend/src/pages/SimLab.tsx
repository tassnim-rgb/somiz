import { useState } from 'react'
import { api } from '../api'
import type { SimulateResponse } from '../types'
import { Chart } from '../components/Chart'
import { StatChip } from '../components/StatChip'

const SCENARIOS = [
  { value: 'healthy', label: 'Sain' },
  { value: 'bearing', label: 'Défaut roulement' },
  { value: 'leakage', label: 'Fuite' },
  { value: 'blockage', label: 'Obstruction' },
]
const DURATIONS = [240, 300, 600, 900]

export function SimLab() {
  const [scenario, setScenario] = useState('bearing')
  const [seed, setSeed] = useState(42)
  const [duration, setDuration] = useState(300)
  const [result, setResult] = useState<SimulateResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [running, setRunning] = useState(false)

  async function run() {
    setRunning(true)
    setError(null)
    setResult(null)
    try {
      const r = await api.simulate({ scenario, seed, duration_s: duration })
      setResult(r)
    } catch (e) {
      setError(String(e))
    } finally {
      setRunning(false)
    }
  }

  const maxSev = result ? Math.max(...result.fault_severity) : 0
  const faults = result
    ? [...new Set(result.dominant_fault.filter((d) => d !== ''))]
    : []

  return (
    <section className="page">
      <h1>Laboratoire de simulation</h1>
      <p className="muted">
        Lance un run SIMULÉ du jumeau physique (Phase 2) à la volée. L&apos;indice de
        santé est calculé par rapport au jumeau sain de même graine (postulat de
        modèle). Aucune donnée réelle.
      </p>

      <div className="card">
        <div className="row wrap gap">
          <label>
            Scénario
            <select value={scenario} onChange={(e) => setScenario(e.target.value)}>
              {SCENARIOS.map((s) => (
                <option key={s.value} value={s.value}>
                  {s.label}
                </option>
              ))}
            </select>
          </label>
          <label>
            Graine
            <input
              type="number"
              value={seed}
              min={0}
              max={2 ** 31 - 1}
              onChange={(e) => setSeed(Number(e.target.value))}
            />
          </label>
          <label>
            Durée (s)
            <select value={duration} onChange={(e) => setDuration(Number(e.target.value))}>
              {DURATIONS.map((d) => (
                <option key={d} value={d}>
                  {d}
                </option>
              ))}
            </select>
          </label>
          <button className="primary" onClick={run} disabled={running}>
            {running ? 'Calcul en cours...' : 'Lancer la simulation'}
          </button>
        </div>
      </div>

      {error ? <p className="error">{error}</p> : null}

      {result ? (
        <>
          <div className="chips">
            <StatChip label="Échantillons simulés" value={result.n_samples.toLocaleString('fr-FR')} />
            <StatChip
              label="Gravité max"
              value={maxSev.toFixed(2)}
              tone={maxSev >= 0.05 ? 'warn' : 'ok'}
            />
            <StatChip
              label="Défauts présents"
              value={faults.length > 0 ? faults.join(', ') : 'Aucun'}
            />
            <StatChip label="Échauffement (s)" value={Math.round(result.warmup_s)} hint="Indice non défini avant cette fenêtre (WARMUP)." />
          </div>

          <div className="grid two">
            <div className="card">
              <h2>Vibration (mm/s)</h2>
              <Chart
                data={[
                  {
                    x: result.t,
                    y: result.vib,
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#1565c0', width: 1.5 },
                  },
                ]}
                layout={{ xaxis: { title: 'Temps (s)' } }}
              />
            </div>
            <div className="card">
              <h2>Indice de santé</h2>
              <Chart
                data={[
                  {
                    x: result.t,
                    y: result.health_index,
                    type: 'scatter',
                    mode: 'lines',
                    line: { color: '#2e7d32', width: 1.5 },
                    connectgaps: false,
                  },
                ]}
                layout={{ yaxis: { range: [0, 110] }, xaxis: { title: 'Temps (s)' } }}
              />
              <p className="muted">Pas de valeur avant l&apos;échauffement : indice non défini (WARMUP).</p>
            </div>
          </div>

          <div className="card">
            <h2>Gravité du défaut (vérité simulée) et pression de refoulement</h2>
            <Chart
              data={[
                {
                  x: result.t,
                  y: result.fault_severity,
                  name: 'Gravité',
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#c62828' },
                  yaxis: 'y',
                },
                {
                  x: result.t,
                  y: result.p_disch,
                  name: 'Pression (bar)',
                  type: 'scatter',
                  mode: 'lines',
                  line: { color: '#6a1b9a' },
                  yaxis: 'y2',
                },
              ]}
              layout={{
                yaxis: { range: [0, 1.05], title: 'Gravité' },
                yaxis2: { overlaying: 'y', side: 'right', title: 'bar' },
                xaxis: { title: 'Temps (s)' },
              }}
            />
          </div>
        </>
      ) : null}
    </section>
  )
}