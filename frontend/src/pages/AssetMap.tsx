import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { AssetDetail, PredictionRow } from '../types'
import { HealthBadge } from '../components/HealthBadge'

function latestHi(rows: PredictionRow[]): number | null {
  let hi: number | null = null
  for (const r of rows) {
    if (r.health_index !== null) hi = r.health_index
  }
  return hi
}

export function AssetMap() {
  const [assets, setAssets] = useState<
    { asset: AssetDetail; hi: number | null }[]
  >([])
  const [error, setError] = useState<string | null>(null)

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
        if (live) setAssets(withHi)
      } catch (e) {
        if (live) setError(String(e))
      }
    })()
    return () => {
      live = false
    }
  }, [])

  return (
    <section className="page">
      <h1>Plan des machines</h1>
      <p className="muted">
        Parc simulé de pompes centrifuges entraînées par moteur. Les classes de
        criticité A/B/C sont un postulat de modèle (tiers de risque du parc).
      </p>
      {error ? <p className="error">{error}</p> : null}
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
              <dl className="kv">
                <dt>Criticité</dt>
                <dd>{crit.class ? String(crit.class) : '-'}</dd>
                <dt>RUL médiane</dt>
                <dd>
                  {crit.rul_p50_days !== undefined
                    ? `${Number(crit.rul_p50_days).toLocaleString('fr-FR')} j`
                    : '-'}
                </dd>
                <dt>P(défaillance à l&apos;horizon)</dt>
                <dd>
                  {crit.p_fail_by_horizon !== undefined
                    ? `${(Number(crit.p_fail_by_horizon) * 100).toFixed(1)} %`
                    : '-'}
                </dd>
                <dt>Risque</dt>
                <dd>
                  {crit.risk !== undefined
                    ? `${Number(crit.risk).toLocaleString('fr-FR')} EUR`
                    : '-'}
                </dd>
              </dl>
            </Link>
          )
        })}
      </div>
    </section>
  )
}