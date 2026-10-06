import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import type { AssetDetail, PredictionRow } from '../types'
import { HealthBadge } from '../components/HealthBadge'
import { ATELIERS } from '../data/ateliers'
import { AtelierTabs } from '../components/AtelierTabs'
import { Plan2D } from '../components/Plan2D'
import { EquipPanel } from '../components/EquipPanel'
import { usePlantLive, useStatusCounts } from '../lib/sim'

function latestHi(rows: PredictionRow[]): number | null {
  let hi: number | null = null
  for (const r of rows) {
    if (r.health_index !== null) hi = r.health_index
  }
  return hi
}

const TOTAL_MACHINES = ATELIERS.reduce((n, a) => n + a.equipment.length, 0)

// Plan des machines — top-down 2D plan derived from the P-01 scans
// (positions approximate), plus the instrumented API asset cards below.
export function AssetMap() {
  const [idx, setIdx] = useState(0)
  const [selId, setSelId] = useState<string | null>(null)
  const [assets, setAssets] = useState<
    { asset: AssetDetail; hi: number | null }[]
  >([])
  const [error, setError] = useState<string | null>(null)

  const live = usePlantLive(idx)
  const counts = useStatusCounts(idx, live)
  const a = ATELIERS[idx]
  const sel = useMemo(() => a.equipment.find((e) => e.id === selId) ?? null, [a, selId])

  useEffect(() => {
    let liveFetch = true
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
        if (liveFetch) setAssets(withHi)
      } catch (e) {
        if (liveFetch) setError(String(e))
      }
    })()
    return () => {
      liveFetch = false
    }
  }, [])

  return (
    <section className="page">
      <h1>Plan des machines</h1>
      <p className="muted">
        Implantation reprise des plans « Plan d&apos;implantation des machines et
        équipements » P-01 ind. 01 (lecture OCR des scans) —{' '}
        <b>positions et surfaces approximatives</b>. {TOTAL_MACHINES} machines et{' '}
        {ATELIERS.reduce((n, x) => n + x.zones.length, 0)} zones dans les quatre
        ateliers ; états, âges et historiques <b>simulés</b> (aucune donnée réelle).
      </p>

      <AtelierTabs
        index={idx}
        onChange={(i) => {
          setIdx(i)
          setSelId(null)
        }}
      />

      <div className="view-grid">
        <Plan2D atelier={a} selectedId={selId} onSelect={setSelId} />
        <EquipPanel eq={sel} counts={counts} />
      </div>

      <p className="faint">
        Source : scans P-01 ind. 01 — DIS · DLOG · DCA (12/05/2024), Centrale
        (01/04/2024). Échelle DIS calée sur la cote d&apos;ensemble 91,41 m ; DLOG,
        DCA et Centrale estimés à partir des surfaces S= imprimées. Survolez une
        machine pour son nom, cliquez pour ouvrir la fiche. États simulés.
      </p>

      <h2>Actifs instrumentés (API simulée)</h2>
      <p className="muted">
        Parc de pompes centrifuges suivi par le backend — jumeaux numériques
        distincts des {TOTAL_MACHINES} machines implantées sur les plans. Les
        classes de criticité A/B/C sont un postulat de modèle (tiers de risque
        du parc).
      </p>
      {error ? <p className="error">{error}</p> : null}
      <div className="grid">
        {assets.map((x) => {
          const crit = x.asset.criticality_json as Record<string, unknown>
          return (
            <Link
              key={x.asset.asset_id}
              to={`/assets/${x.asset.asset_id}`}
              className="card asset-link"
            >
              <div className="row space-between">
                <h3>{x.asset.asset_id}</h3>
                <HealthBadge hi={x.hi} />
              </div>
              <p className="muted">{x.asset.name}</p>
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
    </section>
  )
}
