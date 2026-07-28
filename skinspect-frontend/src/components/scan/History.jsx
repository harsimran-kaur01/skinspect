import { useState, useEffect } from 'react'
import { getScanHistory } from '../../api/scans'
import { Link } from 'react-router-dom'
import ProgressChart from '../progress/ProgressChart'
import ProgressSummary from '../progress/ProgressSummary'

export default function History() {
  const [scans, setScans] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    getScanHistory()
      .then(setScans)
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="p-4">Loading history...</div>

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">📊 Progress Tracking</h1>

      {scans.length === 0 ? (
        <p>No scans yet. <Link to="/scan" className="text-blue-600">Take your first scan</Link></p>
      ) : (
        <>
          <ProgressSummary scans={scans} />
          <ProgressChart scans={scans} />

          <h2 className="text-xl font-semibold mt-8 mb-4">All Scans</h2>
          <ul className="space-y-4">
            {scans.map((s) => (
              <li key={s.id} className="border rounded-lg p-4 hover:shadow transition">
                <div className="flex justify-between items-center">
                  <div>
                    <p className="font-medium">
                      {new Date(s.created_at).toLocaleDateString()} – {new Date(s.created_at).toLocaleTimeString()}
                    </p>
                    <p className="text-sm text-gray-600">
                      Health score: {s.overall_health_score || 'N/A'} | Conditions: {s.conditions.map(c => `${c.condition} (${c.severity})`).join(', ')}
                    </p>
                  </div>
                  <Link to={`/scan/${s.id}`} className="text-blue-600 text-sm">View Details</Link>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}