import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function Nav() {
  const { user, logout } = useAuth()

  return (
    <nav className="border-b border-line bg-paper/80 backdrop-blur-sm sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-6 py-4 flex justify-between items-center">
        <Link to="/" className="font-display text-xl tracking-tight text-ink">
          SkinSpect
        </Link>
        <div className="flex items-center gap-6 text-sm">
          <span className="text-ink/60">{user?.full_name || 'Account'}</span>
          <Link to="/profile" className="text-ink/70 hover:text-sage transition-colors">
            Profile
          </Link>
          <button
            onClick={logout}
            className="text-ink/70 hover:text-alert transition-colors"
          >
            Sign out
          </button>
        </div>
      </div>
    </nav>
  )
}