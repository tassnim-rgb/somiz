import { NavLink, Outlet } from 'react-router-dom'

const NAV = [
  { to: '/', label: 'Vue d\u2019ensemble', end: true },
  { to: '/plan', label: 'Plan des machines' },
  { to: '/assets/A00', label: 'Détail de l\u2019actif' },
  { to: '/maintenance', label: 'Maintenance' },
  { to: '/analyse', label: 'Analyse' },
  { to: '/simulation', label: 'Laboratoire de simulation' },
  { to: '/plan3d', label: 'Vue 3D du site' },
]

export function App() {
  return (
    <div className="layout">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-dot" />
          SOMIZ Digital Twin
        </div>
        <p className="simp">Données SIMULÉES</p>
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
        <div className="sidebar-foot muted">Démo sans lien avec un site réel</div>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  )
}