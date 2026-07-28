export default function ScanResults({ scan }) {
  if (!scan) return null

  const conditions = scan.conditions || []
  const recommendations = scan.recommendations || []

  return (
    <div className="mt-8 border-t pt-6">
      <h2 className="text-2xl font-bold mb-4">Analysis Results</h2>

      <div className="grid md:grid-cols-2 gap-4 mb-6">
        {conditions.map((c, idx) => (
          <div key={idx} className="bg-gray-50 p-4 rounded-lg">
            <h3 className="font-semibold capitalize">{c.condition}</h3>
            <p className="text-sm">Confidence: {(c.confidence * 100).toFixed(0)}%</p>
            <p className="text-sm">Severity: {c.severity || 'N/A'}</p>
            {c.affected_area_percentage !== undefined && (
              <p className="text-sm">Area: {c.affected_area_percentage}%</p>
            )}
            {c.description && <p className="text-sm text-gray-600">{c.description}</p>}
          </div>
        ))}
      </div>

      {scan.overall_health_score !== undefined && (
        <div className="bg-blue-50 p-4 rounded-lg mb-4">
          <span className="font-semibold">Overall Health Score: </span>
          <span className="text-2xl font-bold">{scan.overall_health_score}/100</span>
        </div>
      )}

      {scan.quality_score !== undefined && (
        <p className="text-sm text-gray-500">Image quality: {scan.quality_score}/100</p>
      )}

      {recommendations.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xl font-semibold mb-2">Recommendations</h3>
          <ul className="space-y-2">
            {recommendations.map((r, i) => (
              <li key={i} className="border-l-4 border-blue-500 pl-3">
                <p className="font-medium">{r.title}</p>
                <p className="text-sm text-gray-600">{r.description}</p>
                {r.priority && (
                  <span className={`text-xs font-semibold ${r.priority === 'high' ? 'text-red-600' : 'text-yellow-600'}`}>
                    {r.priority.toUpperCase()}
                  </span>
                )}
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="mt-6 p-4 bg-yellow-50 border-l-4 border-yellow-400 text-sm text-yellow-800">
        ⚠️ This analysis is for informational purposes only and does not replace professional medical advice. Please consult a dermatologist for any concerns.
      </div>
    </div>
  )
}