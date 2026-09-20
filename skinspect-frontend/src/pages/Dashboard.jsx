import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { LineChart, Line, ResponsiveContainer } from 'recharts'
import { useAuth } from '../context/AuthContext'
import { getScanHistory } from '../api/scans'
import Nav from '../components/Nav'
import VerificationBanner from '../components/VerificationBanner'

function greeting() {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}

export default function Dashboard() {
  const { user } = useAuth()
  const [recentScans, setRecentScans] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getScanHistory(6, 0)
      .then((scans) => setRecentScans(scans || []))
      .catch(() => setRecentScans([]))
      .finally(() => setLoading(false))
  }, [])

  const latest = recentScans[0]
  const trendData = [...recentScans]
    .reverse()
    .map((s, i) => ({ i, score: s.overall_health_score ?? 0 }))

  const firstName = user?.full_name?.split(' ')[0]

  return (
    <div className="min-h-screen bg-paper">
      <Nav />


      <div className="max-w-5xl mx-auto px-6 py-16">
        <p className="text-sm text-clay font-medium tracking-wide uppercase mb-3">
          {greeting()}{firstName ? `, ${firstName}` : ''}
        </p>
        <h1 className="font-display text-4xl md:text-5xl text-ink leading-tight mb-4 max-w-xl">
          Your skin, tracked with care.
        </h1>
        <p className="text-ink/60 max-w-md mb-10">
          Run a new scan to see how your skin is changing, or pick up where you left off.
        </p>

        <Link to="/questionnaire" className="btn-primary inline-block mb-14">
          Start New Scan
        </Link>

        {/* Status row */}
        {!loading && (
          <div className="grid sm:grid-cols-2 gap-4 mb-14">
            <div className="card p-6">
              <p className="text-xs uppercase tracking-wide text-ink/50 mb-2">
                Latest Score
              </p>
              {latest ? (
                <p className="stat-number text-4xl text-sage">
                  {latest.overall_health_score}
                  <span className="text-lg text-ink/40">/100</span>
                </p>
              ) : (
                <p className="text-ink/40 text-sm">No scans yet</p>
              )}
            </div>

            <div className="card p-6">
              <p className="text-xs uppercase tracking-wide text-ink/50 mb-2">
                Recent Trend
              </p>
              {trendData.length > 1 ? (
                <div className="h-12">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={trendData}>
                      <Line
                        type="monotone"
                        dataKey="score"
                        stroke="#4F5F4A"
                        strokeWidth={2}
                        dot={false}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              ) : (
                <p className="text-ink/40 text-sm">Not enough data yet</p>
              )}
            </div>
          </div>
        )}

        {/* Navigation cards */}
        <div className="grid md:grid-cols-3 gap-4">
          <Link
            to="/history"
            className="card p-6 hover:border-sage transition-colors group"
          >
            <p className="text-xs uppercase tracking-wide text-ink/40 mb-2">01</p>
            <h3 className="font-display text-lg text-ink mb-1 group-hover:text-sage transition-colors">
              History
            </h3>
            <p className="text-sm text-ink/60">Every past scan, side by side.</p>
          </Link>

          <Link
            to="/derm"
            className="card p-6 hover:border-sage transition-colors group"
          >
            <p className="text-xs uppercase tracking-wide text-ink/40 mb-2">02</p>
            <h3 className="font-display text-lg text-ink mb-1 group-hover:text-sage transition-colors">
              Dermatologists
            </h3>
            <p className="text-sm text-ink/60">Find care near you.</p>
          </Link>

          <Link
            to="/profile"
            className="card p-6 hover:border-sage transition-colors group"
          >
            <p className="text-xs uppercase tracking-wide text-ink/40 mb-2">03</p>
            <h3 className="font-display text-lg text-ink mb-1 group-hover:text-sage transition-colors">
              Profile
            </h3>
            <p className="text-sm text-ink/60">Account and preferences.</p>
          </Link>
        </div>
      </div>
    </div>
  )
}