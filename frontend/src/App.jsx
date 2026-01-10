import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardPro from './pages/DashboardPro'
import TestPage from './pages/TestPage'
import CreativeLab from './pages/CreativeLab'
import Upload from './pages/Upload'
import Analytics from './pages/Analytics'
import PatternDiscovery from './pages/PatternDiscovery'
import InfluencerManager from './pages/InfluencerManager'
import EdTechLanding from './pages/EdTechLanding'

function App() {
  return (
    <Routes>
      {/* EdTech Landing (without Layout - standalone page) */}
      <Route path="/landing" element={<EdTechLanding />} />

      {/* Admin Dashboard (with Layout) */}
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPro />} />
        <Route path="creatives" element={<CreativeLab />} />
        <Route path="upload" element={<Upload />} />
        <Route path="analytics" element={<Analytics />} />
        <Route path="patterns" element={<PatternDiscovery />} />
        <Route path="influencers" element={<InfluencerManager />} />
      </Route>
    </Routes>
  )
}

export default App
