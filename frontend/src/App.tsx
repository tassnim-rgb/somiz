import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { ATELIERS, STATUS_COLORS } from './data/ateliers'
import { hexColor, STATUS_LABEL, useFeed } from './lib/sim'

const NAV = [
  { to: '/', label: 'Vue d\u2019ensemble', end: true },
  { to: '/plan', label: 'Plan des machines' },
  { to: '/assets/A00', label: 'Détail de l\u2019actif' },
  { to: '/maintenance', label: 'Maintenance' },
  { to: '/analyse', label: 'Analyse' },
  { to: '/simulation', label: 'Laboratoire de simulation' },
  { to: '/plan3d', label: 'Vue 3D du site' },
]

const TOTAL_MACHINES = ATELIERS.reduce((n, a) => n + a.equipment.length, 0)
const TOTAL_ZONES = ATELIERS.reduce((n, a) => n + a.zones.length, 0)

const LEGEND: Array<'ok' | 'warn' | 'danger' | 'critical'> = [
  'ok',
  'warn',
  'danger',
  'critical',
]

function Clock() {
  const [time, setTime] = useState(() => new Date().toTimeString().slice(0, 8))
  useEffect(() => {
    const id = window.setInterval(
      () => setTime(new Date().toTimeString().slice(0, 8)),
      1000,
    )
    return () => window.clearInterval(id)
  }, [])
  return <span className="tb-clock">{time}</span>
}

export function App() {
  const feed = useFeed()

  return (
    <div className="layout">
      <header className="topbar">
        <span className="tb-logo">SOMIZ</span>
        <span className="tb-title">Digital Shadow — Maintenance Intelligente</span>
        <div className="tb-spacer" />
        <span className="plan-chip">PLANS P-01 · IND. 01</span>
        <Clock />
        <div className="tb-live">
          <span className="dot" />
          FLUX SIMULÉ ACTIF
        </div>
      </header>

      <aside className="sidebar">
        <div className="brand">
          <span className="brand-dot" />
          SOMIZ Digital Twin
        </div>
        <p className="simp">Données SIMULÉES</p>

        <div className="sidebar-label">Navigation</div>
        <nav>
          {NAV.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) => (isActive ? 'nav-link active' : 'nav-link')}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-divider" />
        <div className="sidebar-label">Implantation P-01</div>
        <div className="side-stats">
          <div className="side-stat">
            <b>{TOTAL_MACHINES}</b>
            <span>machines</span>
          </div>
          <div className="side-stat">
            <b>{TOTAL_ZONES}</b>
            <span>zones</span>
          </div>
          <div className="side-stat">
            <b>{ATELIERS.length}</b>
            <span>ateliers</span>
          </div>
        </div>

        <div className="sidebar-divider" />
        <div className="sidebar-label">États (simulés)</div>
        <div className="legend">
          {LEGEND.map((s) => (
            <div className="legend-item" key={s}>
              <div className="legend-dot" style={{ background: hexColor(STATUS_COLORS[s]) }} />
              {STATUS_LABEL[s]}
            </div>
          ))}
        </div>

        <div className="sidebar-divider" />
        <div className="sidebar-label">Flux d&apos;évènements</div>
        <div className="feed">
          {feed.map((e) => (
            <div className={`event-item event-${e.level}`} key={e.id}>
              <div className="event-time">{e.time}</div>
              <div className="event-text">{e.text}</div>
            </div>
          ))}
        </div>

        <div className="sidebar-note">
          <b>Source</b> — implantation relevée par OCR sur les plans « Plan
          d&apos;implantation des machines et équipements » P-01 ind. 01 : DIS ·
          DLOG · DCA (12/05/2024), Centrale (01/04/2024). Positions et surfaces{' '}
          <b>approximatives</b>. États, âges et historiques <b>simulés</b> — aucune
          donnée de maintenance réelle.
        </div>
        <div className="sidebar-foot">Démo sans lien avec un site réel</div>
      </aside>

      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}
