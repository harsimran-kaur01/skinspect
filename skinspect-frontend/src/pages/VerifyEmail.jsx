import { useEffect, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { verifyEmail } from '../api/auth'

export default function VerifyEmail() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [status, setStatus] = useState('verifying') // verifying | success | error
  const [message, setMessage] = useState('')

  useEffect(() => {
    if (!token) {
      setStatus('error')
      setMessage('Missing verification token.')
      return
    }

    verifyEmail(token)
      .then((data) => {
        setStatus('success')
        setMessage(data.message || 'Email verified successfully.')
      })
      .catch((err) => {
        setStatus('error')
        setMessage(err.response?.data?.detail || 'Verification failed.')
      })
  }, [token])

  return (
    <div className="max-w-md mx-auto mt-24 p-6 text-center">
      {status === 'verifying' && <p>Verifying your email...</p>}

      {status === 'success' && (
        <>
          <h1 className="text-2xl font-bold text-green-700 mb-2">✅ Verified</h1>
          <p className="mb-4">{message}</p>
          <Link to="/login" className="text-blue-600 font-medium">
            Continue to sign in →
          </Link>
        </>
      )}

      {status === 'error' && (
        <>
          <h1 className="text-2xl font-bold text-red-600 mb-2">Verification failed</h1>
          <p className="mb-4">{message}</p>
          <Link to="/profile" className="text-blue-600 font-medium">
            Request a new link from your profile →
          </Link>
        </>
      )}
    </div>
  )
}