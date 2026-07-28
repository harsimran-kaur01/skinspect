import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import VerificationBanner from '../components/VerificationBanner'

export default function Dashboard() {
  const { user, logout } = useAuth()

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow p-4 flex justify-between items-center">
        <h1 className="text-2xl font-bold text-blue-600">SkinSpect</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm">Welcome, {user?.full_name || 'User'}</span>
          <Link to="/profile" className="text-gray-600 text-sm hover:underline">Profile</Link>
          <button onClick={logout} className="text-red-600 text-sm">Logout</button>
        </div>
      </nav>

      <VerificationBanner user={user} />

      <div className="max-w-4xl mx-auto p-6">
        <h2 className="text-3xl font-bold mb-2">Your Skin Health Dashboard</h2>
        <p className="text-gray-600 mb-6">Start your assessment or track your progress</p>

        <div className="grid md:grid-cols-2 gap-4">
          {/* Start Assessment → Goes to Questionnaire */}
          <Link to="/questionnaire" className="bg-blue-50 p-6 rounded-lg shadow hover:shadow-lg transition border-2 border-blue-200">
            <h3 className="text-xl font-semibold text-blue-700">📝 Start New Assessment</h3>
            <p className="text-gray-600">Answer a few questions, then upload a photo for AI analysis</p>
          </Link>

          <Link to="/history" className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
            <h3 className="text-xl font-semibold">📊 History</h3>
            <p className="text-gray-600">View all your past scans and progress</p>
          </Link>

          <Link to="/derm" className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
            <h3 className="text-xl font-semibold">🏥 Dermatologists</h3>
            <p className="text-gray-600">Find nearby skin care professionals</p>
          </Link>

          <Link to="/profile" className="bg-white p-6 rounded-lg shadow hover:shadow-lg transition">
            <h3 className="text-xl font-semibold">👤 Profile</h3>
            <p className="text-gray-600">Manage your account and settings</p>
          </Link>
        </div>
      </div>
    </div>
  )
}