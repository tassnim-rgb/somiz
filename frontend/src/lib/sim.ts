// Live SIMULATED plant processes for the dashboard plan views.
// Ported from the legacy viewer (index.html): sensor AR(1) process, wear
// drift, status transitions and the event feed. Everything here is a demo
// simulation — never real SOMIZ maintenance data.

import { useEffect, useMemo, useState, useSyncExternalStore } from 'react'
import {
  ATELIERS,
  SENSOR_SCALE,
  type Atelier,
  type Sensor,
  type Status,
} from '../data/ateliers'

export const STATUS_ORDER: Status[] = ['ok', 'warn', 'danger', 'critical']

export const STATUS_LABEL: Record<Status, string> = {
  ok: 'Bon état',
  warn: 'À surveiller',
  danger: 'Dégradé',
  critical: 'Critique',
}

export const STATUS_BADGE: Record<Status, [string, string]> = {
  ok: ['badge-ok', 'BON ÉTAT'],
  warn: ['badge-warn', 'À SURVEILLER'],
  danger: ['badge-danger', 'DÉGRADÉ'],
  critical: ['badge-critical', 'CRITIQUE'],
}

export const CRIT_LABEL: Record<string, string> = {
  A: 'Critique (A)',
  B: 'Important (B)',
  C: 'Standard (C)',
}

// 3D motion profile per health state: speed multiplier + roughness (speed
// jitter = stuttering when worn) + glow gain for emissive parts.
export const MOTION: Record<Status, { spd: number; rough: number; glow: number }> = {
  ok: { spd: 1.0, rough: 0.03, glow: 0.6 },
  warn: { spd: 0.85, rough: 0.15, glow: 1.0 },
  danger: { spd: 0.65, rough: 0.45, glow: 1.6 },
  critical: { spd: 0.1, rough: 0.9, glow: 2.4 }, // nearly seized, stuttering
}

export function hexColor(n: number): string {
  return `#${n.toString(16).padStart(6, '0')}`
}

export function countStatuses(a: Atelier): Record<Status, number> {
  const c: Record<Status, number> = { ok: 0, warn: 0, danger: 0, critical: 0 }
  for (const e of a.equipment) c[e.status]++
  return c
}

export function statusFromWear(w: number): Status {
  return w < 0.45 ? 'ok' : w < 0.7 ? 'warn' : w < 0.88 ? 'danger' : 'critical'
}

// Sensor process: mean creeps toward the status-dependent target, smooth
// colored noise (AR(1)), rotary periodicity growing with wear.
export function sensorNext(s: Sensor, status: Status, dt: number): number {
  const target = s.base * SENSOR_SCALE[status]
  s._mean += (target - s._mean) * 0.004
  s._noise = 0.88 * s._noise + (Math.random() * 2 - 1) * 0.12
  s._phase += s._omega * dt
  const overshoot = Math.max(0, s._mean / s.base - 1)
  const wobble = 1 + s._noise * (0.04 + 0.05 * overshoot)
  const periodic = 1 + Math.sin(s._phase) * (0.02 + 0.03 * overshoot)
  return +Math.max(0, s._mean * wobble * periodic).toFixed(1)
}

// ── Event feed (module store, consumed by the sidebar) ─────────────────
export type FeedLevel = 'ok' | 'warn' | 'danger' | 'critical'
export interface FeedItem {
  id: number
  time: string
  text: string
  level: FeedLevel
}

function now(): string {
  return new Date().toTimeString().slice(0, 8)
}

let feedId = 3
let feedItems: FeedItem[] = [
  { id: 3, time: now(), text: 'Synchronisation des 4 ateliers terminée', level: 'ok' },
  {
    id: 2,
    time: now(),
    text: 'Implantation chargée d’après les plans P-01 ind. 01 — positions approximatives',
    level: 'warn',
  },
  { id: 1, time: now(), text: 'Système initialisé — connexion capteurs simulée', level: 'ok' },
]

const feedListeners = new Set<() => void>()

export function pushFeed(text: string, level: FeedLevel): void {
  feedItems = [{ id: ++feedId, time: now(), text, level }, ...feedItems].slice(0, 8)
  feedListeners.forEach((l) => l())
}

function subscribeFeed(cb: () => void): () => void {
  feedListeners.add(cb)
  return () => {
    feedListeners.delete(cb)
  }
}

export function useFeed(): FeedItem[] {
  return useSyncExternalStore(
    subscribeFeed,
    () => feedItems,
    () => feedItems,
  )
}

// ── Live plant simulation hook ─────────────────────────────────────────
// Ticks sensors (2 s) and wear/status (6 s) for the selected atelier,
// mutating the shared plan data (SIMULATED). The returned counter changes
// on every tick so components can re-render / recolour.

export function usePlantLive(idx: number): number {
  const [tick, setTick] = useState(0)

  useEffect(() => {
    const A = ATELIERS[idx]
    let alive = true

    const sensorTimer = window.setInterval(() => {
      if (!alive) return
      const t = Date.now()
      for (const eq of A.equipment) {
        for (const s of eq.sensors) {
          const v = sensorNext(s, eq.status, 2)
          s.value = v
          const thr = s.base * SENSOR_SCALE[eq.status] * 1.25 // +25 % over expected
          if (v > thr && t - (s._lastEvent || 0) > 45000) {
            s._lastEvent = t
            pushFeed(`${eq.name} · ${s.label}: ${v} ${s.unit} — pic de mesure`, 'warn')
          }
        }
      }
      setTick((x) => x + 1)
    }, 2000)

    const healthTimer = window.setInterval(() => {
      if (!alive) return
      for (const eq of A.equipment) {
        const prev = eq.status
        const rate =
          0.0035 * (1 + eq.age / 30) * (eq.criticality === 'A' ? 1.3 : eq.criticality === 'B' ? 1.1 : 1)
        eq._wear = Math.min(1, eq._wear + rate * Math.random())
        if (Math.random() < 0.006) {
          // rare shock / fault spike
          eq._wear = Math.min(1, eq._wear + 0.1 + Math.random() * 0.15)
          pushFeed(`${eq.name} — pic de dégradation capté`, 'warn')
        }
        const ns = statusFromWear(eq._wear)
        if (ns !== prev) {
          eq.status = ns
          const worse = STATUS_ORDER.indexOf(ns) > STATUS_ORDER.indexOf(prev)
          const verbs: Record<Status, string> = {
            ok: 'retour à la normale',
            warn: 'passage en surveillance',
            danger: 'dégradation détectée',
            critical: 'ALERTE CRITIQUE',
          }
          const level: FeedLevel = worse
            ? ns === 'critical'
              ? 'critical'
              : ns === 'danger'
                ? 'danger'
                : 'warn'
            : 'ok'
          pushFeed(`${eq.name} — ${verbs[ns]}`, level)
        }
      }
      // occasional corrective maintenance on the most worn machine
      if (Math.random() < 0.055) {
        const target = A.equipment
          .filter((e) => e.status !== 'ok')
          .sort((a, b) => b._wear - a._wear)
          .find((e) => e._wear > 0.6)
        if (target) {
          target._wear = 0.05 + Math.random() * 0.15
          target.status = 'ok'
          pushFeed(`${target.name} — maintenance corrective effectuée`, 'ok')
        }
      }
      setTick((x) => x + 1)
    }, 6000)

    return () => {
      alive = false
      window.clearInterval(sensorTimer)
      window.clearInterval(healthTimer)
    }
  }, [idx])

  return tick
}

// Status counts, recomputed whenever the live simulation ticks.
export function useStatusCounts(idx: number, live: number): Record<Status, number> {
  return useMemo(() => countStatuses(ATELIERS[idx]), [idx, live])
}
