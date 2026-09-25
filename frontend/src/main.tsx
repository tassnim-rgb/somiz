import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { App } from './App'
import { Overview } from './pages/Overview'
import { AssetMap } from './pages/AssetMap'
import { AssetDetail } from './pages/AssetDetail'
import { MaintenancePlanner } from './pages/MaintenancePlanner'
import { Analytics } from './pages/Analytics'
import { SimLab } from './pages/SimLab'
import { Plant3D } from './pages/Plant3D'
import './styles.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route element={<App />}>
          <Route index element={<Overview />} />
          <Route path="/plan" element={<AssetMap />} />
          <Route path="/assets/:id" element={<AssetDetail />} />
          <Route path="/maintenance" element={<MaintenancePlanner />} />
          <Route path="/analyse" element={<Analytics />} />
          <Route path="/simulation" element={<SimLab />} />
          <Route path="/plan3d" element={<Plant3D />} />
        </Route>
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)