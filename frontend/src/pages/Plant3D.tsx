import { useEffect, useMemo, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { ATELIERS, STATUS_COLORS } from '../data/ateliers'
import { animateMachines, buildMachine, recolorGroup, type SceneItem } from '../lib/build3d'
import { usePlantLive, useStatusCounts } from '../lib/sim'
import { AtelierTabs } from '../components/AtelierTabs'
import { EquipPanel } from '../components/EquipPanel'

// Vue 3D du site — plan-derived plant view (same content as the legacy
// viewer): zones, 98 machines across the four ateliers, projected zone
// labels, hover/click raycasting. Positions approximate (OCR, P-01 ind. 01);
// states simulated by usePlantLive.
export function Plant3D() {
  const [idx, setIdx] = useState(0)
  const [selId, setSelId] = useState<string | null>(null)

  const live = usePlantLive(idx)
  const counts = useStatusCounts(idx, live)
  const a = ATELIERS[idx]
  const sel = useMemo(() => a.equipment.find((e) => e.id === selId) ?? null, [a, selId])

  const mountRef = useRef<HTMLDivElement>(null)
  const tipRef = useRef<HTMLDivElement>(null)
  const itemsRef = useRef<SceneItem[]>([])
  const labelElsRef = useRef<(HTMLDivElement | null)[]>([])
  const labelPosRef = useRef<THREE.Vector3[]>([])

  // ── scene (rebuilt when the atelier changes) ─────────────────────────
  useEffect(() => {
    const mount = mountRef.current
    if (!mount) return
    const A = ATELIERS[idx]

    const renderer = new THREE.WebGLRenderer({ antialias: true })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(mount.clientWidth || 800, mount.clientHeight || 520)
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    mount.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    scene.background = new THREE.Color(0x05070a)
    scene.fog = new THREE.FogExp2(0x05070a, 0.0048)

    const camera = new THREE.PerspectiveCamera(
      42,
      (mount.clientWidth || 800) / (mount.clientHeight || 520),
      0.1,
      1000,
    )

    // industrial lighting rig: cool ambient + warm key + cyan rim
    scene.add(new THREE.AmbientLight(0x223344, 1.4))
    const key = new THREE.DirectionalLight(0xfff1d8, 1.1)
    key.castShadow = true
    key.shadow.mapSize.set(2048, 2048)
    scene.add(key)
    scene.add(key.target)
    const rim = new THREE.DirectionalLight(0x00c2d4, 0.5)
    rim.position.set(-50, 30, -50)
    scene.add(rim)

    // fit key light + shadow frustum to this atelier's footprint
    key.target.position.set(A.w / 2, 0, A.d / 2)
    key.position.set(A.w / 2 + 25, 75, A.d / 2 + 30)
    const ext = Math.max(A.w, A.d) * 0.72 + 10
    key.shadow.camera.left = -ext
    key.shadow.camera.right = ext
    key.shadow.camera.top = ext
    key.shadow.camera.bottom = -ext
    key.shadow.camera.updateProjectionMatrix()

    const grid = new THREE.GridHelper(220, 44, 0x18222c, 0x18222c)
    grid.position.y = -0.01
    scene.add(grid)

    // floor slab + cyan edges
    const floor = new THREE.Mesh(
      new THREE.BoxGeometry(A.w, 0.3, A.d),
      new THREE.MeshStandardMaterial({ color: 0x0c1218, metalness: 0.2, roughness: 0.85 }),
    )
    floor.position.set(A.w / 2, -0.15, A.d / 2)
    floor.receiveShadow = true
    scene.add(floor)
    const edges = new THREE.LineSegments(
      new THREE.EdgesGeometry(new THREE.BoxGeometry(A.w + 0.2, 0.35, A.d + 0.2)),
      new THREE.LineBasicMaterial({ color: 0x00c2d4, transparent: true, opacity: 0.35 }),
    )
    edges.position.set(A.w / 2, -0.15, A.d / 2)
    scene.add(edges)

    // zone pads (plan areas)
    for (const z of A.zones) {
      const zm = new THREE.Mesh(
        new THREE.BoxGeometry(z.w, 0.08, z.d),
        new THREE.MeshStandardMaterial({ color: z.color, transparent: true, opacity: 0.95, roughness: 0.9 }),
      )
      zm.position.set(z.x + z.w / 2, 0.04, z.z + z.d / 2)
      zm.receiveShadow = true
      scene.add(zm)
      const ze = new THREE.LineSegments(
        new THREE.EdgesGeometry(new THREE.BoxGeometry(z.w, 0.08, z.d)),
        new THREE.LineBasicMaterial({ color: 0x1c252e, transparent: true, opacity: 0.6 }),
      )
      ze.position.copy(zm.position)
      scene.add(ze)
    }

    // roof spotlights for atmosphere
    for (const [px, pz] of [
      [A.w * 0.25, A.d * 0.25],
      [A.w * 0.75, A.d * 0.25],
      [A.w * 0.25, A.d * 0.75],
      [A.w * 0.75, A.d * 0.75],
    ]) {
      const s = new THREE.PointLight(0xfff1d8, 0.6, 60, 2)
      s.position.set(px, 22, pz)
      scene.add(s)
    }

    // machines + beacons + invisible hit boxes
    const items: SceneItem[] = []
    for (const eq of A.equipment) {
      const color = STATUS_COLORS[eq.status]
      const { group, h } = buildMachine(eq, color)
      group.position.set(eq.x + eq.w / 2, 0, eq.z + eq.d / 2)
      scene.add(group)

      const beacon = new THREE.Mesh(
        new THREE.SphereGeometry(0.35, 10, 10),
        new THREE.MeshStandardMaterial({ color, emissive: color, emissiveIntensity: 1.2 }),
      )
      beacon.position.set(eq.x + eq.w / 2, h + 1.2, eq.z + eq.d / 2)
      scene.add(beacon)

      const hitBox = new THREE.Mesh(
        new THREE.BoxGeometry(eq.w * 1.3, h * 1.3, eq.d * 1.3),
        new THREE.MeshBasicMaterial({ visible: false }),
      )
      hitBox.position.set(eq.x + eq.w / 2, h * 0.5, eq.z + eq.d / 2)
      scene.add(hitBox)

      items.push({ eq, group, beacon, hitBox, h })
    }
    itemsRef.current = items

    // projected zone-label anchors (elements are rendered by React)
    labelPosRef.current = A.zones.map(
      (z) => new THREE.Vector3(z.x + z.w / 2, 0.15, z.z + z.d / 2),
    )

    // camera on an orbit around the atelier centre
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.enablePan = false
    controls.maxPolarAngle = Math.PI / 2.15
    controls.minDistance = 15
    controls.maxDistance = 260
    const cx = A.w / 2
    const cz = A.d / 2
    controls.target.set(cx, 0, cz)
    const radius = Math.max(A.w, A.d) * 1.15
    const theta = 0.6
    const phi = 0.85
    camera.position.set(
      cx + radius * Math.sin(phi) * Math.sin(theta),
      radius * Math.cos(phi),
      cz + radius * Math.sin(phi) * Math.cos(theta),
    )
    camera.lookAt(cx, 0, cz)
    controls.update()

    // hover / click raycasting
    const raycaster = new THREE.Raycaster()
    const pointer = new THREE.Vector2()
    let hoveredItem: SceneItem | null = null
    let selectedItem: SceneItem | null = null
    let tipShown = false

    function pick(e: PointerEvent | MouseEvent): SceneItem | null {
      const r = renderer.domElement.getBoundingClientRect()
      pointer.x = ((e.clientX - r.left) / r.width) * 2 - 1
      pointer.y = -((e.clientY - r.top) / r.height) * 2 + 1
      raycaster.setFromCamera(pointer, camera)
      const hits = raycaster.intersectObjects(
        items.map((it) => it.hitBox),
        false,
      )
      if (!hits.length) return null
      return items.find((it) => it.hitBox === hits[0].object) ?? null
    }

    function setScale(item: SceneItem, s: number): void {
      item.group.scale.setScalar(s)
      item.beacon.scale.setScalar(s)
    }

    function onMove(e: PointerEvent): void {
      const item = pick(e)
      if (item) {
        if (hoveredItem !== item) {
          if (hoveredItem && hoveredItem !== selectedItem) setScale(hoveredItem, 1)
          hoveredItem = item
          if (item !== selectedItem) setScale(item, 1.06)
        }
        const t = tipRef.current
        if (t) {
          const r = mount!.getBoundingClientRect()
          t.style.display = 'block'
          t.style.left = `${e.clientX - r.left + 14}px`
          t.style.top = `${e.clientY - r.top - 10}px`
          t.textContent = item.eq.name
        }
        tipShown = true
        renderer.domElement.style.cursor = 'pointer'
      } else {
        if (hoveredItem && hoveredItem !== selectedItem) setScale(hoveredItem, 1)
        hoveredItem = null
        if (tipShown) {
          const t = tipRef.current
          if (t) t.style.display = 'none'
          tipShown = false
        }
        renderer.domElement.style.cursor = 'default'
      }
    }

    function onClick(e: MouseEvent): void {
      const item = pick(e)
      if (!item) return
      if (selectedItem) setScale(selectedItem, 1)
      selectedItem = item
      setScale(item, 1.1)
      setSelId(item.eq.id)
    }

    renderer.domElement.addEventListener('pointermove', onMove)
    renderer.domElement.addEventListener('click', onClick)

    // project zone labels to screen space every frame (arrow fn: keeps the
    // mount narrowing from the guard above)
    const _v = new THREE.Vector3()
    const _c = new THREE.Vector3()
    const updateZoneLabels = (): void => {
      const w = mount.clientWidth
      const h = mount.clientHeight
      const poses = labelPosRef.current
      for (let i = 0; i < poses.length; i++) {
        const el = labelElsRef.current[i]
        if (!el) continue
        _c.copy(poses[i]).applyMatrix4(camera.matrixWorldInverse)
        if (_c.z > -1) {
          el.style.opacity = '0'
          continue // behind / too close
        }
        _v.copy(poses[i]).project(camera)
        const x = (_v.x * 0.5 + 0.5) * w
        const y = (-_v.y * 0.5 + 0.5) * h
        el.style.left = `${x}px`
        el.style.top = `${y}px`
        el.style.opacity = x < -40 || x > w + 40 || y < -20 || y > h + 20 ? '0' : '1'
      }
    }

    const ro = new ResizeObserver(() => {
      const w = mount.clientWidth
      const h = mount.clientHeight
      if (!w || !h) return
      camera.aspect = w / h
      camera.updateProjectionMatrix()
      renderer.setSize(w, h)
    })
    ro.observe(mount)

    let lastT = performance.now()
    renderer.setAnimationLoop(() => {
      const now = performance.now()
      controls.update()
      animateMachines(items, now - lastT)
      lastT = now
      updateZoneLabels()
      renderer.render(scene, camera)
    })

    return () => {
      renderer.setAnimationLoop(null)
      ro.disconnect()
      renderer.domElement.removeEventListener('pointermove', onMove)
      renderer.domElement.removeEventListener('click', onClick)
      controls.dispose()
      scene.traverse((obj) => {
        const mesh = obj as THREE.Mesh
        if (mesh.geometry) mesh.geometry.dispose()
        const mat = mesh.material as THREE.Material | THREE.Material[] | undefined
        if (Array.isArray(mat)) mat.forEach((m) => m.dispose())
        else if (mat) mat.dispose()
      })
      renderer.dispose()
      if (renderer.domElement.parentNode === mount) mount.removeChild(renderer.domElement)
      itemsRef.current = []
    }
  }, [idx])

  // recolour machines whenever the live simulation ticks a status change
  useEffect(() => {
    for (const it of itemsRef.current) {
      const hex = STATUS_COLORS[it.eq.status]
      recolorGroup(it.group, hex)
      const bm = it.beacon.material as THREE.MeshStandardMaterial
      bm.color.setHex(hex)
      bm.emissive.setHex(hex)
    }
  }, [live])

  return (
    <section className="page">
      <h1>Vue 3D du site (simulation)</h1>
      <p className="muted">
        Implantation reprise des plans « Plan d&apos;implantation des machines et
        équipements » P-01 ind. 01 (lecture OCR) — <b>positions approximatives</b>.
        Les états visibles sont <b>simulés</b> ; les jumeaux numériques
        instrumentés du parc sont détaillés dans les pages Détail et Analyse.
      </p>

      <AtelierTabs
        index={idx}
        onChange={(i) => {
          setIdx(i)
          setSelId(null)
        }}
      />

      <div className="view-grid">
        <div className="scene" ref={mountRef} style={{ height: 540 }}>
          <div className="zone-labels">
            {a.zones.map((z, i) => (
              <div
                className="zone-label"
                key={`${idx}-${i}`}
                ref={(el) => {
                  labelElsRef.current[i] = el
                }}
              >
                <span className="zl-name">{z.name}</span>
                {z.area ? (
                  <span className="zl-area">{z.area.replace(/^S\s*=\s*/, '')}</span>
                ) : null}
              </div>
            ))}
          </div>
          <div className="grid-label">
            SOMIZ-SPA · Arzew, Oran · implantation P-01 — positions approximatives ·
            états simulés
          </div>
          <div className="hint">🖱 Clic gauche : orbite · Scroll : zoom · Clic équipement : détails</div>
          <div className="tooltip" ref={tipRef} style={{ display: 'none' }} />
        </div>

        <EquipPanel eq={sel} counts={counts} />
      </div>

      <p className="faint">
        Source : scans P-01 ind. 01 — DIS · DLOG · DCA (12/05/2024), Centrale
        (01/04/2024). Échelle DIS calée sur la cote d&apos;ensemble 91,41 m ; DLOG,
        DCA et Centrale estimés à partir des surfaces S= imprimées (aucune cote
        lisible au scan). États, âges et historiques simulés — aucune donnée de
        maintenance réelle.
      </p>
    </section>
  )
}
