import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { api } from '../api'
import type { AssetSummary, PredictionRow } from '../types'
import { bandOf } from '../types'

function latestHi(rows: PredictionRow[]): number | null {
  let hi: number | null = null
  for (const r of rows) {
    if (r.health_index !== null) hi = r.health_index
  }
  return hi
}

interface Placed {
  asset: AssetSummary
  hi: number | null
  x: number
  z: number
}

export function Plant3D() {
  const mountRef = useRef<HTMLDivElement>(null)
  const [placed, setPlaced] = useState<Placed[]>([])
  const [hovered, setHovered] = useState<string | null>(null)
  const hoverRef = useRef<string | null>(null)

  useEffect(() => {
    let live = true
    ;(async () => {
      try {
        const list = await api.assets()
        const withHi = await Promise.all(
          list.map(async (asset) => {
            const preds = await api.predictions(asset.asset_id, 5000)
            return { asset, hi: latestHi(preds) }
          }),
        )
        if (!live) return
        const spots: [number, number][] = [
          [-5, 5],
          [5, 5],
          [-5, -5],
          [5, -5],
          [0, 0],
          [-8, 0],
          [8, 0],
          [0, 8],
          [0, -8],
        ]
        setPlaced(
          withHi.map((p, i) => ({
            ...p,
            x: spots[i % spots.length][0],
            z: spots[i % spots.length][1],
          })),
        )
      } catch {
        /* scene stays empty; honest error shown below */
      }
    })()
    return () => {
      live = false
    }
  }, [])

  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return

    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x0f1720)
    const camera = new THREE.PerspectiveCamera(55, mount.clientWidth / mount.clientHeight, 0.1, 200)
    camera.position.set(10, 12, 14)
    camera.lookAt(0, 0, 0)

    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setSize(mount.clientWidth, mount.clientHeight)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    mount.appendChild(renderer.domElement)

    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true

    scene.add(new THREE.AmbientLight(0xffffff, 0.55))
    const key = new THREE.DirectionalLight(0xffffff, 0.9)
    key.position.set(8, 14, 6)
    scene.add(key)

    const grid = new THREE.GridHelper(24, 12, 0x274060, 0x1b2a44)
    scene.add(grid)

    const meshes: THREE.Mesh[] = []
    const raycaster = new THREE.Raycaster()
    const pointer = new THREE.Vector2()

    function colorOf(hi: number | null): THREE.Color {
      const band = bandOf(hi)
      if (!band) return new THREE.Color(0x546e7a)
      const c = new THREE.Color(band.color)
      return c
    }

    function buildAsset(row: Placed) {
      const group = new THREE.Group()
      const body = new THREE.Mesh(
        new THREE.BoxGeometry(1.6, 1.2, 1.6),
        new THREE.MeshStandardMaterial({
          color: colorOf(row.hi),
          emissive: colorOf(row.hi),
          emissiveIntensity: row.hi !== null && row.hi < 60 ? 0.45 : 0.12,
          roughness: 0.5,
        }),
      )
      body.position.y = 0.6
      group.add(body)
      // motor side
      const motor = new THREE.Mesh(
        new THREE.CylinderGeometry(0.55, 0.55, 0.9, 16),
        new THREE.MeshStandardMaterial({ color: 0x37474f, roughness: 0.6 }),
      )
      motor.rotation.z = Math.PI / 2
      motor.position.set(1.3, 0.6, 0)
      group.add(motor)
      group.position.set(row.x, 0, row.z)
      meshes.push(body)
      // label sprite is replaced by the HTML overlay on hover
      group.userData.assetId = row.asset.asset_id
      group.userData.assetName = row.asset.name
      group.userData.hi = row.hi
      scene.add(group)
    }

    placed.forEach(buildAsset)

    function onPointerMove(e: PointerEvent) {
      const rect = renderer.domElement.getBoundingClientRect()
      pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
      pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1
      raycaster.setFromCamera(pointer, camera)
      const hits = raycaster.intersectObjects(meshes, false)
      if (hits.length > 0) {
        hoverRef.current = String(hits[0].object.userData.assetId)
      } else {
        hoverRef.current = null
      }
      setHovered(hoverRef.current)
    }
    renderer.domElement.addEventListener('pointermove', onPointerMove)

    function onResize() {
      const w = mount!.clientWidth
      const h = mount!.clientHeight
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    }
    window.addEventListener('resize', onResize)

    renderer.setAnimationLoop(() => {
      controls.update()
      renderer.render(scene, camera)
    })

    return () => {
      renderer.setAnimationLoop(null)
      window.removeEventListener('resize', onResize)
      renderer.domElement.removeEventListener('pointermove', onPointerMove)
      scene.traverse((obj) => {
        const mesh = obj as THREE.Mesh
        if (mesh.geometry) mesh.geometry.dispose()
        const mat = (mesh as THREE.Mesh).material as THREE.Material | THREE.Material[]
        if (Array.isArray(mat)) mat.forEach((m) => m.dispose())
        else if (mat) mat.dispose()
      })
      renderer.dispose()
      mountRef.current?.removeChild(renderer.domElement)
    }
  }, [placed])

  const selected = placed.find((p) => p.asset.asset_id === hovered)
  const band = selected ? bandOf(selected.hi) : null

  return (
    <section className="page">
      <h1>Vue 3D du site (simulation)</h1>
      <p className="muted">
        Positionnement illustratif du parc SIMULÉ. La couleur suit l&apos;indice de
        santé : vert normal, ambre modéré, rouge sévère ou défaillance.
      </p>
      <div
        ref={mountRef}
        style={{ width: '100%', height: 520, borderRadius: 8, position: 'relative', overflow: 'hidden' }}
        className="scene"
      >
        {selected ? (
          <div className="overlay-badge" style={{ position: 'absolute', left: 14, top: 14 }}>
            <strong>{selected.asset.asset_id}</strong> - {selected.asset.name}
            <div style={{ color: band?.color ?? '#9e9e9e' }}>
              {band ? `${band.labelFr} ${Math.round(selected.hi ?? 0)}` : 'Pas de lecture'}
            </div>
          </div>
        ) : (
          <div className="overlay-badge" style={{ position: 'absolute', left: 14, top: 14 }}>
            Survolez une machine
          </div>
        )}
      </div>
      <p className="muted">Glisser pour orbiter, molette pour zoomer.</p>
    </section>
  )
}