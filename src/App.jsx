import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import DashboardPage from './pages/DashboardPage'
import LeaderboardPage from './pages/LeaderboardPage'
import ModelDetailPage from './pages/ModelDetailPage'
import PlotsPage from './pages/PlotsPage'
import AboutPage from './pages/AboutPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<DashboardPage />} />
          <Route path="leaderboard" element={<LeaderboardPage />} />
          <Route path="model/:activationName" element={<ModelDetailPage />} />
          <Route path="plots" element={<PlotsPage />} />
          <Route path="about" element={<AboutPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
