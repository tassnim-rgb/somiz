import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import {
  HEALTH_BANDS,
  bandOf,
  type AssetDetail,
  type MaintenancePlanRow,
  type PredictionRow,
} from '../types'
import { Chart } from '../components/Chart'
import { StatChip } from '../components/StatChip'
import { HealthBadge } from '../components/HealthBadge'

interface AssetHealth {
  asset: AssetDetail
  hi: number | null
}

function latestHi(rows: PredictionRow[]): number | null {
  let hi: number | null = null
  for (const r of rows) {
    if (r.health_index !== null) hi = r.health_index
  }
  return hi
}

export function Overview() {
  const [assets, setAssets] = useState<AssetHealth[]>([])
  const [plan, setPlan] = useState<MaintenancePlanRow | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let live = true
    ;(async () => {
      try {
        const list = await api.assets()
        const withHi = await Promise.all(
          list.map(async (asset) => {
            const [detail, preds] = await Promise.all([
              api.asset(asset.asset_id),
              api.predictions(asset.asset_id, 5000),
            ])
            return { asset: detail, hi: latestHi(preds) }
          }),
        )
        const plans = await api.plans(true)
        if (!live) return
        setAssets(withHi)
        setPlan(plans[0] ?? null)
      } catch (e) {
        if (live) setError(String(e))
      } finally {
        if (live) setLoading(false)
      }
    })()
    return () => {
      live = false
    }
  }, [])

  if (loading) return <p className="muted">Chargement des données simulées...</p>
  if (error) return <p className="error">Backend injoignable : {error}</p>

  const stages = HEALTH_BANDS.map((b) => ({
    ...b,
    count: assets.filter((a) => {
      const band = bandOf(a.hi)
      return band?.key === b.key
    }).length,
  }))
  const detected = assets.filter((a) => {
    const band = bandOf(a.hi)
    return band !== null && band.from < 60
  }).length

  return (
    <section className="page">
      <h1>Vue d&apos;ensemble</h1>
      <p className="muted">
        Plateforme de démonstration. Toutes les données sont SIMULÉES, issues
        du jumeau numérique (aucune installation réelle).
      </p>

      <div className="chips">
        <StatChip label="Actifs simulés" value={assets.length} />
        <StatChip
          label="Actifs dégradés ou critiques (indice &lt; 60)"
          value={detected}
          tone={detected > 0 ? 'warn' : 'ok'}
        />
        <StatChip
          label="Coût planifié (objectif MILP, EUR)"
          value={plan ? plan.objective_value?.toLocaleString('fr-FR') : '-'}
          hint="Coût total du plan de maintenance optimisé (données simulées)."
        />
        <StatChip
          label="Horizon du plan (jours)"
          value={plan ? plan.horizon_days : '-'}
        />
      </div>

      <div className="card">
        <h2>Répartition de l&apos;indice de santé (état le plus récent)</h2>
        <Chart
          data={[
            {
              x: stages.map((s) => s.labelFr),
              y: stages.map((s) => s.count),
              type: 'bar',
              marker: { color: stages.map((s) => s.color) },
            },
          ]}
          layout={{ yaxis: { dtick: 1, range: [0, Math.max(2, ...stages.map((s) => s.count + 0.5))] } }}
        />
      </div>

      <div className="grid">
        {assets.map((a) => {
          const crit = a.asset.criticality_json as Record<string, unknown>
          return (
            <Link key={a.asset.asset_id} to={`/assets/${a.asset.asset_id}`} className="card asset-link">
              <div className="row space-between">
                <h3>{a.asset.asset_id}</h3>
                <HealthBadge hi={a.hi} />
              </div>
              <p className="muted">{a.asset.name}</p>
              {crit.class ? (
                <p className="muted">
                  Classe de criticité {String(crit.class)} - risque{' '}
                  {Number(crit.risk).toLocaleString('fr-FR')} EUR
                </p>
              ) : null}
            </Link>
          )
        })}
      </div>

      {plan ? (
        <div className="card">
          <h2>Plan de maintenance (simulation MILP)</h2>
          <table>
            <thead>
              <tr>
                <th>Actif</th>
                <th>Jour planifié</th>
                <th>Horizon</th>
                <th>Solveur</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(plan.plan_json).map(([aid, day]) => (
                <tr key={aid}>
                  <td>{aid}</td>
                  <td>{day === null ? 'Aucune intervention' : `Jour ${day}`}</td>
                  <td>{plan.horizon_days} jours</td>
                  <td>{plan.solver}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </section>
  )
}