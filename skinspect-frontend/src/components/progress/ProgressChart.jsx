import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'

export default function ProgressChart({ scans }) {
  // scans: array of SkinScanResponse objects
  const data = scans.map(s => ({
    date: new Date(s.created_at).toLocaleDateString(),
    score: s.overall_health_score || 0,
    acne: s.conditions.find(c => c.condition === 'acne')?.confidence || 0,
    wrinkles: s.conditions.find(c => c.condition === 'wrinkles')?.confidence || 0,
  })).reverse() // oldest to newest

  if (data.length < 2) {
    return <p className="text-gray-500 text-center">Need at least two scans to show progress.</p>
  }

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-2">Skin Health Trend</h3>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis domain={[0, 100]} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="score" stroke="#2563eb" strokeWidth={2} name="Health Score" />
          <Line type="monotone" dataKey="acne" stroke="#dc2626" strokeWidth={1.5} name="Acne Confidence" />
          <Line type="monotone" dataKey="wrinkles" stroke="#9333ea" strokeWidth={1.5} name="Wrinkle Confidence" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}