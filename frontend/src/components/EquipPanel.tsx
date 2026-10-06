import type { Equip, Status } from '../data/ateliers'
import { CRIT_LABEL, STATUS_BADGE } from '../lib/sim'

// Right-hand equipment panel (mirrors the legacy viewer's #panel):
// header + details / empty state + per-atelier status counters.
export function EquipPanel(props: {
  eq: Equip | null
  counts: Record<Status, number>
}) {
  const { eq, counts } = props

  return (
    <aside className="panel">
      <div className="panel-header">
        <div className="ph-label">Équipement sélectionné</div>
        <div className="ph-name">{eq ? eq.name : '—'}</div>
        <div className="ph-type">
          {eq ? `${eq.type} · ${eq.id}` : 'Cliquez sur un équipement'}
        </div>
      </div>

      <div className="panel-body">
        {eq ? (
          <>
            <div className="stat-row">
              <span className="stat-label">État de santé</span>
              <span className={`status-badge ${STATUS_BADGE[eq.status][0]}`}>
                {STATUS_BADGE[eq.status][1]}
              </span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Criticité</span>
              <span className="stat-val">{CRIT_LABEL[eq.criticality] ?? eq.criticality}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Âge</span>
              <span className="stat-val">{eq.age} ans</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Dernière maint.</span>
              <span className="stat-val">{eq.lastMaint}</span>
            </div>
            <div className="stat-row">
              <span className="stat-label">Prochaine maint.</span>
              <span className="stat-val">{eq.nextMaint}</span>
            </div>

            <div className="section-title">Capteurs en direct</div>
            <div className="sensor-grid">
              {eq.sensors.map((s) => (
                <div className="sensor-box" key={s.label}>
                  <div className="sv">
                    {s.value}
                    <small> {s.unit}</small>
                  </div>
                  <div className="sl">{s.label}</div>
                </div>
              ))}
            </div>

            <div className="section-title">Historique d&apos;interventions</div>
            {eq.history.map((h) => {
              const [date, ...rest] = h.split(' — ')
              return (
                <div className="history-item" key={h}>
                  <span className="history-date">{date}</span>
                  <span className="history-text">{rest.join(' — ')}</span>
                </div>
              )
            })}

            <div className="panel-note">
              États, âges et historiques simulés pour la démonstration — aucune donnée
              de maintenance réelle n&apos;est représentée. Position de l&apos;équipement
              relevée sur le plan P-01 ind. 01 (approximatif).
            </div>
          </>
        ) : (
          <div className="empty-state">
            <div className="es-icon">⬡</div>
            <div className="es-text">
              Sélectionnez un équipement
              <br />
              dans la vue pour afficher son
              <br />
              état simulé en direct
            </div>
          </div>
        )}
      </div>

      <div className="stats-bar">
        <div className="stat-chip">
          <div className="sc-val sc-ok">{counts.ok}</div>
          <div className="sc-label">Bon état</div>
        </div>
        <div className="stat-chip">
          <div className="sc-val sc-warn">{counts.warn}</div>
          <div className="sc-label">Surveiller</div>
        </div>
        <div className="stat-chip">
          <div className="sc-val sc-danger">{counts.danger}</div>
          <div className="sc-label">Dégradé</div>
        </div>
        <div className="stat-chip">
          <div className="sc-val sc-critical">{counts.critical}</div>
          <div className="sc-label">Critique</div>
        </div>
      </div>
    </aside>
  )
}
