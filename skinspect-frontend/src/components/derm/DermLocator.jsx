import { useState, useEffect, useRef } from 'react'
import { getNearbyDermatologists } from '../../api/derm'

function directionsUrl(lat, lng, destinationLabel) {
  const destination = lat && lng ? `${lat},${lng}` : encodeURIComponent(destinationLabel)
  return `https://www.google.com/maps/dir/?api=1&destination=${destination}`
}

export default function DermLocator() {
  const [position, setPosition] = useState(null)
  const [clinics, setClinics] = useState([])
  const [loading, setLoading] = useState(false)
  const [slowLoad, setSlowLoad] = useState(false)
  const [error, setError] = useState('')
  const [searchedRadiusKm, setSearchedRadiusKm] = useState(null)
  const [isDermSpecific, setIsDermSpecific] = useState(true)
  const slowTimerRef = useRef(null)

  useEffect(() => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setPosition({
            lat: pos.coords.latitude,
            lng: pos.coords.longitude,
          })
        },
        () => {
          setError('Unable to get location. Please enable GPS.')
        }
      )
    } else {
      setError('Geolocation not supported.')
    }
  }, [])

  useEffect(() => {
    if (!position) return

    setLoading(true)
    setSlowLoad(false)
    setError('')

    // If this is taking more than 5s, tell the user why instead of
    // leaving a bare "Loading..." on screen.
    slowTimerRef.current = setTimeout(() => setSlowLoad(true), 5000)

    getNearbyDermatologists(position.lat, position.lng)
      .then((data) => {
        setClinics(data.clinics || [])
        setSearchedRadiusKm(data.searched_radius_km ?? null)
        setIsDermSpecific(data.is_dermatology_specific ?? true)
      })
      .catch((err) => {
        if (err.code === 'ECONNABORTED') {
          setError('This is taking too long. The clinic directory service may be slow right now — try again in a moment.')
        } else {
          setError('Failed to fetch clinics.')
        }
      })
      .finally(() => {
        setLoading(false)
        clearTimeout(slowTimerRef.current)
      })

    return () => clearTimeout(slowTimerRef.current)
  }, [position])

  if (error) return <div className="p-4 text-red-500">{error}</div>
  if (!position) return <div className="p-4">Getting your location...</div>

  return (
    <div className="max-w-3xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-1">Nearby Dermatologists</h1>
      <p className="text-sm text-gray-500 mb-4">
        Showing the closest dermatology-focused clinics we could find near you.
      </p>

      {loading && (
        <p>
          Loading...
          {slowLoad && (
            <span className="block text-sm text-gray-500 mt-1">
              Still searching — this can take up to 20-30 seconds if the clinic
              directory service is slow to respond.
            </span>
          )}
        </p>
      )}

      {!loading && clinics.length > 0 && !isDermSpecific && (
        <div className="mb-4 p-3 rounded bg-amber-50 border border-amber-200 text-amber-800 text-sm">
          We couldn't find any dermatology-specific listings within{' '}
          {searchedRadiusKm} km, so these are general clinics and hospitals
          instead — you may want to call ahead and confirm they offer
          dermatology care before visiting.
        </div>
      )}

      {clinics.length === 0 && !loading && (
        <p>
          No clinics found near your location
          {searchedRadiusKm ? ` within ${searchedRadiusKm} km` : ''}. This area
          may not be well-mapped on OpenStreetMap yet.
        </p>
      )}

      {clinics.length > 0 && (
        <ul className="space-y-2">
          {clinics.map((c) => (
            <li key={c.place_id} className="border p-3 rounded">
              <h3 className="font-bold">{c.name}</h3>
              {c.address && <p className="text-sm text-gray-600">{c.address}</p>}
              <p className="text-sm text-gray-600">{c.distance_km} km away</p>
              {c.phone && <p className="text-sm text-gray-600">📞 {c.phone}</p>}
              {c.opening_hours && (
                <p className="text-sm text-gray-600">🕒 {c.opening_hours}</p>
              )}
              <div className="flex gap-4 mt-2">
                <a
                  href={directionsUrl(c.lat, c.lng, c.name)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 text-sm font-medium"
                >
                  Get Directions →
                </a>
                {c.website && (
                  <a
                    href={c.website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-600 text-sm font-medium"
                  >
                    Visit Website
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}