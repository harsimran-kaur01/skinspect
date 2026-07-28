import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

export default function Transition() {
  const navigate = useNavigate()
  const location = useLocation()
  const { nextPath, message } = location.state || {}

  useEffect(() => {
    if (!nextPath) {
      // Guard against someone landing here directly with no state
      navigate('/', { replace: true })
      return
    }
    const timer = setTimeout(() => navigate(nextPath, { replace: true }), 2000)
    return () => clearTimeout(timer)
  }, [navigate, nextPath])

  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="text-center">
        <div className="animate-spin h-10 w-10 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
        <p className="text-xl">{message || 'Preparing your analysis...'}</p>
      </div>
    </div>
  )
}