import { useEffect, useState } from 'react'
import { api } from '../api'
import type { MaintenanceEventRow, MaintenancePlanRow } from '../types'
import { Chart } from '../components/Chart'
import { StatChip } from '../components/StatChip'

export function MaintenancePlanner() {
  const [plan, setPlan] = useState<MaintenancePlanRow | null>(null)
  const [events, setEvents] = useState<MaintenanceEventRow[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let live = true
    ;(async () => {
      try {
        const [plans, evts] = await Promise.all([api.plans(true), api.events()])
        if (!live) return
        setPlan(plans[0] ?? null)
        setEvents(evts)
      } catch (e) {
        if (live) setError(String(e))
      }
    })()
    return () => {
      live = false
    }
  }, [])

  const schedule = Object.entries(plan?.plan_json ?? {})
  const maxDay = Math.max(1, ...schedule.map(([, d]) => (d ?? 0) + 1))

  return (
    <section className="page">
      <h1>Planificateur de maintenance</h1>
      <p className="muted">
        Plan généré par le solveur MILP (scipy / HiGHS) sur des entrées SIMULÉES
        (RUL et coûts). Aucune garantie sur un site réel.
      </p>
      {error ? <p className="error">{error}</p> : null}
      {plan ? (
        <>
          <div className="chips">
            <StatChip
              label="Coût total planifié (EUR)"
              value={plan.objective_value?.toLocaleString('fr-FR') ?? '-'}
            />
            <StatChip label="Horizon" value={`${plan.horizon_days} jours`} />
            <StatChip label="Solveur" value={plan.solver} />
            <StatChip
              label="Interventions planifiées"
              value={schedule.filter(([, d]) => d !== null).length}
            />
          </div>

          <div className="card">
            <h2>Calendrier des interventions (jour J depuis la génération)</h2>
            <Chart
              data={[
                {
                  y: schedule.map(([aid]) => aid),
                  x: schedule.map(([, d]) => (d ?? 0) + 1),
                  type: 'bar',
                  orientation: 'h',
                  marker: { color: '#1565c0' },
                  text: schedule.map(([, d]) => (d === null ? 'Aucune' : `Jour ${d}`)),
                  textposition: 'outside',
                },
              ]}
              layout={{
                xaxis: { title: 'Jour', dtick: 1, range: [0, maxDay + 0.4] },
                margin: { l: 64, r: 24, t: 32, b: 40 },
              }}
            />
            <p className="muted">
              Fenêtres sans maintenance : {String((plan.constraints_json.no_maintenance_days ?? []))}.
              Capacité : {String(plan.constraints_json.capacity_per_day)} intervention(s) par jour.
            </p>
          </div>

          <div className="card">
            <h2>Événements de maintenance (simulés)</h2>
            <table>
              <thead>
                <tr>
                  <th>Actif</th>
                  <th>Date prévue</th>
                  <th>Action</th>
                  <th>Coût (EUR)</th>
                  <th>Durée (h)</th>
                  <th>Statut</th>
                </tr>
              </thead>
              <tbody>
                {events.map((e, i) => (
                  <tr key={i}>
                    <td>{e.asset_id}</td>
                    <td>
                      {e.scheduled_at
                        ? new Date(e.scheduled_at).toLocaleDateString('fr-FR')
                        : '-'}
                    </td>
                    <td>{e.action_type}</td>
                    <td>{e.cost?.toLocaleString('fr-FR')}</td>
                    <td>{e.duration_h}</td>
                    <td>{e.outcome ?? 'prévu'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      ) : (
        <p className="muted">Aucun plan enregistré.</p>
      )}
    </section>
  )
}