import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import DashboardPro from './pages/DashboardPro'
import CreativeLab from './pages/CreativeLab'
import Upload from './pages/Upload'
import Analytics from './pages/Analytics'
import PatternDiscovery from './pages/PatternDiscovery'
import InfluencerManager from './pages/InfluencerManager'
import EdTechLanding from './pages/EdTechLanding'

function App() {
  return (
    <AuthProvider>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/landing" element={<EdTechLanding />} />

        {/* Protected routes */}
        <Route path="/" element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }>
          <Route index element={<Navigate to="/creative-lab" replace />} />
          <Route path="dashboard" element={<DashboardPro />} />
          <Route path="creative-lab" element={<CreativeLab />} />
          <Route path="upload" element={<Upload />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="patterns" element={<PatternDiscovery />} />
          <Route path="influencers" element={<InfluencerManager />} />
        </Route>
      </Routes>
    </AuthProvider>
  )
}

export default App
