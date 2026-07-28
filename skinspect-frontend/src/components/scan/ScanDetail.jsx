import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { getScan } from '../../api/scans'
import ScanResults from './ScanResults'

export default function ScanDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [scan, setScan] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    getScan(id)
      .then(setScan)
      .catch((err) => {
        setError(err.response?.data?.detail || 'Failed to load scan')
        console.error(err)
      })
      .finally(() => setLoading(false))
  }, [id])

  if (loading) return <div className="p-6 text-center">Loading scan details...</div>
  if (error) return <div className="p-6 text-red-500">{error}</div>
  if (!scan) return <div className="p-6 text-gray-500">Scan not found</div>

  return (
    <div className="max-w-3xl mx-auto p-6">
      <button
        onClick={() => navigate(-1)}
        className="mb-4 text-blue-600 hover:underline text-sm"
      >
        ← Back
      </button>
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-center mb-4">
          <h1 className="text-2xl font-bold">Scan Details</h1>
          <span className="text-sm text-gray-500">
            {new Date(scan.created_at).toLocaleString()}
          </span>
        </div>
        <ScanResults scan={scan} />
      </div>
    </div>
  )
}