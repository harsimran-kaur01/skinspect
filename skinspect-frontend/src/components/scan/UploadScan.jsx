import { useState, useRef } from 'react'
import { uploadScan } from '../../api/scans'
import ScanResults from './ScanResults'

export default function UploadScan() {
  const [file, setFile] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [guidance, setGuidance] = useState('')
  const [qualityPassed, setQualityPassed] = useState(false)
  const [error, setError] = useState('')
  const fileInputRef = useRef(null)

  const validateImage = (file) => {
    const reader = new FileReader()
    reader.onload = (e) => {
      const img = new Image()
      img.onload = () => {
        if (img.width < 200 || img.height < 200) {
          setGuidance('Image too small. Please use a clear face photo.')
          setQualityPassed(false)
          return
        }
        setGuidance('Image looks good. Proceed with analysis.')
        setQualityPassed(true)
        setPreview(e.target.result)
      }
      img.src = e.target.result
    }
    reader.readAsDataURL(file)
  }

  const handleFileChange = (e) => {
    const selected = e.target.files[0]
    if (selected) {
      setError('')
      setFile(selected)
      validateImage(selected)
    }
  }

  const handleUpload = async () => {
    if (!file || !qualityPassed) return

    setLoading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      const data = await uploadScan(formData)
      setResult(data.scan)
    } catch (err) {
      // err.response exists for HTTP error responses (4xx/5xx with a body).
      // If it's missing, this was a network-level failure (no connection,
      // CORS block, timeout) — show a distinct message for that case
      // instead of a blank/undefined error.
      const message = err.response?.data?.detail
        ?? (err.request ? 'Could not reach the server. Check your connection and try again.' : 'Upload failed')
      setError(message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-2">Upload Your Photo</h1>
      <p className="text-gray-600 mb-6">Take a clear selfie in good lighting for the best results.</p>

      <div className="border-2 border-dashed rounded-lg p-8 text-center">
        <input
          type="file"
          accept="image/*"
          capture="environment"
          ref={fileInputRef}
          onChange={handleFileChange}
          className="hidden"
        />
        <button
          onClick={() => fileInputRef.current.click()}
          className="bg-blue-600 text-white px-6 py-3 rounded hover:bg-blue-700"
        >
          📸 Upload or Take Photo
        </button>
        {preview && (
          <div className="mt-4">
            <img src={preview} alt="Preview" className="max-h-80 mx-auto rounded" />
            <p className="mt-2 text-sm text-gray-600">{guidance}</p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-3 rounded bg-red-50 border border-red-200 text-red-700 text-sm">
          {error}
        </div>
      )}

      {qualityPassed && (
        <button
          onClick={handleUpload}
          disabled={loading}
          className="mt-4 w-full bg-green-600 text-white p-3 rounded hover:bg-green-700 disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : '🔬 Analyze My Skin'}
        </button>
      )}

      {result && <ScanResults scan={result} />}
    </div>
  )
}
