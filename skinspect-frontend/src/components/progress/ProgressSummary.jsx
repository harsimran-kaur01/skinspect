import { useMemo } from 'react'

export default function ProgressSummary({ scans }) {
  // Compute stats from scans array
  const stats = useMemo(() => {
    if (scans.length < 2) return null

    const first = scans[scans.length - 1]  // oldest
    const last = scans[0]  // newest
    const scoreDiff = last.overall_health_score - first.overall_health_score

    const getConditionChange = (name) => {
      const firstC = first.conditions.find(c => c.condition === name)
      const lastC = last.conditions.find(c => c.condition === name)
      if (!firstC || !lastC) return null
      const diff = lastC.confidence - firstC.confidence
      return diff
    }

    const acneChange = getConditionChange('acne')
    const wrinkleChange = getConditionChange('wrinkles')

    return {
      scoreDiff,
      acneChange,
      wrinkleChange,
      totalScans: scans.length,
      firstDate: first.created_at,
      lastDate: last.created_at,
    }
  }, [scans])

  if (!stats) {
    return <p className="text-gray-500 text-center">Upload at least two scans to see progress.</p>
  }

  const { scoreDiff, acneChange, wrinkleChange, totalScans, firstDate, lastDate } = stats

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <div className="bg-white p-4 rounded-lg shadow">
        <p className="text-sm text-gray-500">Overall Health</p>
        <p className={`text-2xl font-bold ${scoreDiff > 0 ? 'text-green-600' : 'text-red-600'}`}>
          {scoreDiff > 0 ? '+' : ''}{scoreDiff}
        </p>
        <p className="text-xs text-gray-400">from {new Date(firstDate).toLocaleDateString()} to today</p>
      </div>
      <div className="bg-white p-4 rounded-lg shadow">
        <p className="text-sm text-gray-500">Acne Confidence</p>
        <p className={`text-2xl font-bold ${acneChange !== null && acneChange < 0 ? 'text-green-600' : acneChange > 0 ? 'text-red-600' : 'text-gray-500'}`}>
          {acneChange !== null ? (acneChange < 0 ? '↓' : '↑') + Math.abs(acneChange).toFixed(2) : '—'}
        </p>
        <p className="text-xs text-gray-400">{acneChange !== null ? (acneChange < 0 ? 'improved' : 'worsened') : 'no data'}</p>
      </div>
      <div className="bg-white p-4 rounded-lg shadow">
        <p className="text-sm text-gray-500">Wrinkle Confidence</p>
        <p className={`text-2xl font-bold ${wrinkleChange !== null && wrinkleChange < 0 ? 'text-green-600' : wrinkleChange > 0 ? 'text-red-600' : 'text-gray-500'}`}>
          {wrinkleChange !== null ? (wrinkleChange < 0 ? '↓' : '↑') + Math.abs(wrinkleChange).toFixed(2) : '—'}
        </p>
        <p className="text-xs text-gray-400">{wrinkleChange !== null ? (wrinkleChange < 0 ? 'improved' : 'worsened') : 'no data'}</p>
      </div>
    </div>
  )
}