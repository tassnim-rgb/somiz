import { ATELIERS } from '../data/ateliers'

// Atelier selector shared by the 2D plan and the 3D view.
export function AtelierTabs(props: { index: number; onChange: (i: number) => void }) {
  return (
    <div className="tabs" role="tablist" aria-label="Ateliers">
      {ATELIERS.map((a, i) => (
        <button
          key={a.name}
          role="tab"
          aria-selected={i === props.index}
          className={i === props.index ? 'tab active' : 'tab'}
          onClick={() => props.onChange(i)}
        >
          <span>{a.name}</span>
          <small>
            {a.surface} · {a.equipment.length} équip. · {a.zones.length} zones
          </small>
        </button>
      ))}
    </div>
  )
}
