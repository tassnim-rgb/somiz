// Machine archetype geometry for the 3D plan view — ported from the legacy
// viewer (index.html buildLathe/buildMill/… builders). Each archetype returns
// a THREE.Group fitted to (w, h, d); moving parts register in
// group.userData.anim so animateMachines() can drive them per health state.

import * as THREE from 'three'
import type { Equip, Status } from '../data/ateliers'
import { MOTION } from './sim'

interface Rotor {
  m: THREE.Object3D
  axis: 'x' | 'y' | 'z'
  base: number
  phase: number
  speed: number
}
interface Osc {
  m: THREE.Object3D
  axis: 'x' | 'y' | 'z'
  base: number
  amp: number
  phase: number
  speed: number
}
interface Pulse {
  mat: THREE.MeshStandardMaterial
  baseI: number
  phase: number
  speed: number
}
export interface Anim {
  rotors: Rotor[]
  oscs: Osc[]
  pulses: Pulse[]
}

export interface SceneItem {
  eq: Equip
  group: THREE.Group
  beacon: THREE.Mesh
  hitBox: THREE.Mesh
  h: number
}

// deterministic 0..1 hash — stable geometry across rebuilds / StrictMode
export function hash01(s: string): number {
  let h = 2166136261
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return ((h >>> 0) % 100000) / 100000
}

export function statusBaseHeight(mtype: string): number {
  const table: Record<string, number> = {
    lathe: 3.2,
    mill: 3.8,
    saw: 3.5,
    press: 4.2,
    compressor: 4.6,
    oven: 4.0,
    drill: 3.4,
    vent: 3.0,
    generic: 3.0,
  }
  return table[mtype] ?? 3.0
}

function newAnim(): Anim {
  return { rotors: [], oscs: [], pulses: [] }
}

function machineMaterial(color: number, roughnessC?: number): THREE.MeshStandardMaterial {
  const m = new THREE.MeshStandardMaterial({
    color,
    metalness: 0.65,
    roughness: roughnessC ?? 0.45,
    emissive: color,
    emissiveIntensity: 0.12,
  })
  m.userData.statusColored = true
  return m
}
function darkSteel(): THREE.MeshStandardMaterial {
  return new THREE.MeshStandardMaterial({ color: 0x2a3038, metalness: 0.8, roughness: 0.35 })
}
function accentMat(color: number): THREE.MeshStandardMaterial {
  const m = new THREE.MeshStandardMaterial({
    color,
    metalness: 0.3,
    roughness: 0.5,
    emissive: color,
    emissiveIntensity: 0.55,
  })
  m.userData.statusColored = true
  return m
}

function regRotor(a: Anim, m: THREE.Object3D, axis: 'x' | 'y' | 'z', speed: number): void {
  a.rotors.push({ m, axis, base: m.rotation[axis], phase: 0, speed })
}
function regOsc(a: Anim, m: THREE.Object3D, axis: 'x' | 'y' | 'z', amp: number, speed: number, seed: number): void {
  a.oscs.push({ m, axis, base: m.position[axis], amp, phase: seed * Math.PI * 2, speed })
}
function regPulse(a: Anim, mat: THREE.MeshStandardMaterial, speed: number, seed: number): void {
  a.pulses.push({ mat, baseI: mat.emissiveIntensity, phase: seed * Math.PI * 2 * 1.7, speed })
}

function finalize(g: THREE.Group): THREE.Group {
  g.children.forEach((c) => {
    c.castShadow = true
  })
  return g
}

type Bld = (w: number, h: number, d: number, color: number, seed: number) => THREE.Group

const buildLathe: Bld = (w, h, d, color, seed) => {
  const g = new THREE.Group()
  const anim = newAnim()
  const bed = new THREE.Mesh(new THREE.BoxGeometry(w, h * 0.35, d * 0.5), darkSteel())
  bed.position.set(0, h * 0.18, 0)
  g.add(bed)
  const headstock = new THREE.Mesh(new THREE.BoxGeometry(w * 0.22, h * 0.7, d * 0.6), machineMaterial(color))
  headstock.position.set(-w * 0.32, h * 0.35, 0)
  g.add(headstock)
  const chuck = new THREE.Mesh(new THREE.CylinderGeometry(d * 0.18, d * 0.18, w * 0.08, 16), darkSteel())
  chuck.rotation.z = Math.PI / 2
  chuck.position.set(-w * 0.18, h * 0.4, 0)
  g.add(chuck)
  const work = new THREE.Mesh(new THREE.CylinderGeometry(d * 0.1, d * 0.1, w * 0.3, 12), machineMaterial(color, 0.6))
  work.rotation.z = Math.PI / 2
  work.position.set(-w * 0.02, h * 0.4, 0)
  g.add(work)
  const rail = new THREE.Mesh(new THREE.BoxGeometry(w * 0.55, h * 0.05, d * 0.08), accentMat(color))
  rail.position.set(w * 0.05, h * 0.36, 0)
  g.add(rail)
  regRotor(anim, chuck, 'z', 6)
  regRotor(anim, work, 'z', 6)
  regPulse(anim, rail.material as THREE.MeshStandardMaterial, 2, seed)
  g.userData.anim = anim
  return finalize(g)
}

const buildMill: Bld = (w, h, d, color, seed) => {
  const g = new THREE.Group()
  const anim = newAnim()
  const base = new THREE.Mesh(new THREE.BoxGeometry(w * 0.9, h * 0.3, d * 0.9), darkSteel())
  base.position.set(0, h * 0.15, 0)
  g.add(base)
  const column = new THREE.Mesh(new THREE.BoxGeometry(w * 0.3, h * 0.85, d * 0.35), machineMaterial(color))
  column.position.set(-w * 0.2, h * 0.42, -d * 0.15)
  g.add(column)
  const head = new THREE.Mesh(new THREE.BoxGeometry(w * 0.22, h * 0.18, d * 0.22), accentMat(color))
  head.position.set(w * 0.05, h * 0.62, d * 0.05)
  g.add(head)
  const spindle = new THREE.Mesh(new THREE.CylinderGeometry(d * 0.04, d * 0.04, h * 0.18, 12), darkSteel())
  spindle.position.set(w * 0.05, h * 0.5, d * 0.05)
  g.add(spindle)
  regRotor(anim, spindle, 'y', 8)
  regOsc(anim, head, 'y', h * 0.05, 0.8, seed)
  regOsc(anim, spindle, 'y', h * 0.05, 0.8, seed)
  regPulse(anim, head.material as THREE.MeshStandardMaterial, 2.4, seed)
  g.userData.anim = anim
  return finalize(g)
}

const buildSaw: Bld = (w, h, d, color, seed) => {
  const g = new THREE.Group()
  const anim = newAnim()
  const base = new THREE.Mesh(new THREE.BoxGeometry(w * 0.85, h * 0.25, d * 0.6), darkSteel())
  base.position.set(0, h * 0.12, 0)
  g.add(base)
  const arm = new THREE.Mesh(new THREE.BoxGeometry(w * 0.15, h * 0.9, d * 0.15), machineMaterial(color))
  arm.position.set(-w * 0.3, h * 0.45, 0)
  g.add(arm)
  const bladeRing = new THREE.Mesh(new THREE.TorusGeometry(d * 0.32, d * 0.03, 8, 24), accentMat(color))
  bladeRing.position.set(w * 0.05, h * 0.55, 0)
  g.add(bladeRing)
  const hub = new THREE.Mesh(new THREE.CylinderGeometry(d * 0.08, d * 0.08, 0.12, 10), darkSteel())
  hub.rotation.x = Math.PI / 2
  hub.position.copy(bladeRing.position)
  g.add(hub)
  regRotor(anim, bladeRing, 'z', 5)
  regRotor(anim, hub, 'z', 5)
  regPulse(anim, bladeRing.material as THREE.MeshStandardMaterial, 3, seed)
  g.userData.anim = anim
  return finalize(g)
}

const buildPress: Bld = (w, h, d, color, seed) => {
  const g = new THREE.Group()
  const anim = newAnim()
  const base = new THREE.Mesh(new THREE.BoxGeometry(w, h * 0.2, d), darkSteel())
  base.position.set(0, h * 0.1, 0)
  g.add(base)
  const colL = new THREE.Mesh(new THREE.BoxGeometry(w * 0.12, h * 0.95, d * 0.12), darkSteel())
  colL.position.set(-w * 0.38, h * 0.5, -d * 0.38)
  g.add(colL)
  const colR = colL.clone()
  colR.position.x = w * 0.38
  g.add(colR)
  const colL2 = colL.clone()
  colL2.position.z = d * 0.38
  g.add(colL2)
  const colR2 = colR.clone()
  colR2.position.z = d * 0.38
  g.add(colR2)
  const ram = new THREE.Mesh(new THREE.BoxGeometry(w * 0.7, h * 0.18, d * 0.7), machineMaterial(color))
  ram.position.set(0, h * 0.75, 0)
  g.add(ram)
  const indicator = new THREE.Mesh(new THREE.SphereGeometry(d * 0.06, 8, 8), accentMat(color))
  indicator.position.set(0, h * 0.95, 0)
  g.add(indicator)
  regOsc(anim, ram, 'y', h * 0.12, 1.1, seed)
  regPulse(anim, indicator.material as THREE.MeshStandardMaterial, 4, seed)
  g.userData.anim = anim
  return finalize(g)
}

const buildCompressor: Bld = (w, h, d, color, seed) => {
  const g = new THREE.Group()
  const anim = newAnim()
  const tank = new THREE.Mesh(new THREE.CylinderGeometry(d * 0.4, d * 0.4, h * 0.9, 16), machineMaterial(color))
  tank.position.set(0, h * 0.45, 0)
  g.add(tank)
  const cap1 = new THREE.Mesh(
    new THREE.SphereGeometry(d * 0.4, 16, 16, 0, Math.PI * 2, 0, Math.PI / 2),
    machineMaterial(color),
  )
  cap1.position.set(0, h * 0.9, 0)
  g.add(cap1)
  const legs = new THREE.Mesh(new THREE.BoxGeometry(w * 0.9, h * 0.08, d * 0.9), darkSteel())
  legs.position.set(0, h * 0.04, 0)
  g.add(legs)
  const gauge = new THREE.Mesh(new THREE.CylinderGeometry(d * 0.08, d * 0.08, d * 0.04, 12), accentMat(color))
  gauge.rotation.x = Math.PI / 2
  gauge.position.set(0, h * 0.6, d * 0.42)
  g.add(gauge)
  regPulse(anim, gauge.material as THREE.MeshStandardMaterial, 1.6, seed)
  regPulse(anim, tank.material as THREE.MeshStandardMaterial, 2.2, seed)
  g.userData.anim = anim
  return finalize(g)
}

const buildOven: Bld = (w, h, d, color, seed) => {
  const g = new THREE.Group()
  const anim = newAnim()
  const body = new THREE.Mesh(new THREE.BoxGeometry(w, h * 0.85, d), darkSteel())
  body.position.set(0, h * 0.42, 0)
  g.add(body)
  const door = new THREE.Mesh(new THREE.BoxGeometry(w * 0.05, h * 0.6, d * 0.6), accentMat(color))
  door.position.set(w * 0.48, h * 0.42, 0)
  g.add(door)
  const chimney = new THREE.Mesh(new THREE.CylinderGeometry(d * 0.1, d * 0.1, h * 0.4, 10), darkSteel())
  chimney.position.set(0, h * 1.05, 0)
  g.add(chimney)
  regPulse(anim, door.material as THREE.MeshStandardMaterial, 0.5, seed)
  regPulse(anim, chimney.material as THREE.MeshStandardMaterial, 0.8, seed)
  g.userData.anim = anim
  return finalize(g)
}

const buildDrill: Bld = (w, h, d, color, seed) => {
  const g = new THREE.Group()
  const anim = newAnim()
  const base = new THREE.Mesh(new THREE.BoxGeometry(w * 0.7, h * 0.15, d * 0.7), darkSteel())
  base.position.set(0, h * 0.08, 0)
  g.add(base)
  const col = new THREE.Mesh(new THREE.CylinderGeometry(d * 0.08, d * 0.08, h * 0.9, 10), machineMaterial(color))
  col.position.set(-w * 0.15, h * 0.5, 0)
  g.add(col)
  const headBox = new THREE.Mesh(new THREE.BoxGeometry(w * 0.3, h * 0.18, d * 0.3), accentMat(color))
  headBox.position.set(0, h * 0.65, 0)
  g.add(headBox)
  const bit = new THREE.Mesh(new THREE.CylinderGeometry(d * 0.02, d * 0.02, h * 0.3, 6), darkSteel())
  bit.position.set(0, h * 0.4, 0)
  g.add(bit)
  regRotor(anim, bit, 'y', 10)
  regOsc(anim, bit, 'y', h * 0.08, 1.4, seed)
  regOsc(anim, headBox, 'y', h * 0.03, 1.4, seed)
  regPulse(anim, headBox.material as THREE.MeshStandardMaterial, 3, seed)
  g.userData.anim = anim
  return finalize(g)
}

const buildVent: Bld = (_w, h, d, color, seed) => {
  const g = new THREE.Group()
  const anim = newAnim()
  const housing = new THREE.Mesh(new THREE.CylinderGeometry(d * 0.45, d * 0.45, h * 0.6, 12), darkSteel())
  housing.rotation.z = Math.PI / 2
  housing.position.set(0, h * 0.5, 0)
  g.add(housing)
  const fanRing = new THREE.Mesh(new THREE.TorusGeometry(d * 0.3, d * 0.04, 8, 20), accentMat(color))
  fanRing.rotation.y = Math.PI / 2
  fanRing.position.set(d * 0.32, h * 0.5, 0)
  g.add(fanRing)
  const hub = new THREE.Mesh(new THREE.SphereGeometry(d * 0.07, 8, 8), darkSteel())
  hub.position.copy(fanRing.position)
  g.add(hub)
  regRotor(anim, fanRing, 'z', 7)
  regRotor(anim, hub, 'z', 7)
  regPulse(anim, fanRing.material as THREE.MeshStandardMaterial, 2.8, seed)
  g.userData.anim = anim
  return finalize(g)
}

const buildGeneric: Bld = (w, h, d, color, seed) => {
  const g = new THREE.Group()
  const anim = newAnim()
  const body = new THREE.Mesh(new THREE.BoxGeometry(w, h * 0.8, d), machineMaterial(color))
  body.position.set(0, h * 0.4, 0)
  g.add(body)
  const accent = new THREE.Mesh(new THREE.BoxGeometry(w * 1.02, h * 0.06, d * 1.02), accentMat(color))
  accent.position.set(0, h * 0.78, 0)
  g.add(accent)
  regPulse(anim, accent.material as THREE.MeshStandardMaterial, 2, seed)
  g.userData.anim = anim
  return finalize(g)
}

const BUILDERS: Record<string, Bld> = {
  lathe: buildLathe,
  mill: buildMill,
  saw: buildSaw,
  press: buildPress,
  compressor: buildCompressor,
  oven: buildOven,
  drill: buildDrill,
  vent: buildVent,
  generic: buildGeneric,
}

// Build one machine group; height is deterministic per machine id.
export function buildMachine(eq: Equip, color: number): { group: THREE.Group; h: number } {
  const h = statusBaseHeight(eq.mtype) * (0.85 + hash01(eq.id) * 0.3)
  const builder = BUILDERS[eq.mtype] ?? buildGeneric
  const group = builder(eq.w, h, eq.d, color, hash01(eq.id))
  return { group, h }
}

// Recolour every status-dependent material in a machine group.
export function recolorGroup(group: THREE.Group, color: number): void {
  group.traverse((obj) => {
    const mesh = obj as THREE.Mesh
    const mat = mesh.material as THREE.MeshStandardMaterial | undefined
    if (mat && mat.userData.statusColored) {
      mat.color.setHex(color)
      mat.emissive.setHex(color)
    }
  })
}

// Advance rotors / oscillations / emissive pulses at a speed set by health.
export function animateMachines(items: SceneItem[], dtMs: number): void {
  const sec = Math.min(0.1, dtMs / 1000)
  for (const item of items) {
    const prof = MOTION[item.eq.status as Status]
    const rough = prof.rough * (Math.random() * 2 - 1)
    const spd = Math.max(0, prof.spd * (1 + rough))
    const a = item.group.userData.anim as Anim | undefined
    if (!a) continue
    for (const r of a.rotors) {
      r.phase += sec * spd * r.speed
      r.m.rotation[r.axis] = r.base + r.phase
    }
    for (const o of a.oscs) {
      o.phase += sec * spd * o.speed
      o.m.position[o.axis] = o.base + Math.sin(o.phase) * o.amp * (0.4 + 0.6 * prof.glow)
    }
    for (const p of a.pulses) {
      p.phase += sec * p.speed
      const glow = (Math.sin(p.phase) + 1) / 2
      p.mat.emissiveIntensity = p.baseI * (1 + glow * prof.glow)
    }
  }
}
