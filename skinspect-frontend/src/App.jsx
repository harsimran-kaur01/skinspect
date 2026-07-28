import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './context/AuthContext'
import Login from './components/auth/Login'
import Register from './components/auth/Register'
import Dashboard from './pages/Dashboard'
import ScanPage from './pages/ScanPage'
import HistoryPage from './pages/HistoryPage'
import DermPage from './pages/DermPage'
import ProfilePage from './pages/ProfilePage'
import QuestionnaireForm from './components/questionnaire/QuestionnaireForm'
import Transition from './components/Transition'
import ScanDetail from './components/scan/ScanDetail'
import VerifyEmail from './pages/VerifyEmail'


function ProtectedRoute({ children }) {
  const { user, loading } = useAuth()
  if (loading) return <div className="flex items-center justify-center min-h-screen">Loading...</div>
  if (!user) return <Navigate to="/login" replace />
  return children
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/questionnaire" element={<ProtectedRoute><QuestionnaireForm /></ProtectedRoute>} />
          <Route path="/transition" element={<ProtectedRoute><Transition /></ProtectedRoute>} />
          <Route path="/scan" element={<ProtectedRoute><ScanPage /></ProtectedRoute>} />
          <Route path="/scan/:id" element={<ProtectedRoute><ScanDetail /></ProtectedRoute>} />
          <Route path="/history" element={<ProtectedRoute><HistoryPage /></ProtectedRoute>} />
          <Route path="/derm" element={<ProtectedRoute><DermPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
          <Route path="/verify-email" element={<VerifyEmail />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}

export default App