import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { Link, useNavigate } from 'react-router-dom'

export default function Register() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [error, setError] = useState('')
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
  e.preventDefault()
  setError('') // Clear any previous error

  try {
    await register(email, password, fullName)
    navigate('/dashboard')
  } catch (err) {
    // FastAPI validation errors
    const detail = err.response?.data?.detail

    if (Array.isArray(detail)) {
      // Combine all validation messages into one string
      setError(
        detail
          .map((d) => d.msg || JSON.stringify(d))
          .join('. ')
      )
    } else if (typeof detail === 'string') {
      // Custom backend error message
      setError(detail)
    } else {
      // Fallback error
      setError('Registration failed. Please check your inputs.')
    }
  }
}

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <h2 className="text-3xl font-bold text-center">Create Account</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="text"
            placeholder="Full Name"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full p-3 border rounded"
            required
          />
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-3 border rounded"
            required
          />
          <input
            type="password"
            placeholder="Password (min 8 chars)"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-3 border rounded"
            required
            minLength={8}
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button type="submit" className="w-full bg-blue-600 text-white p-3 rounded hover:bg-blue-700">
            Register
          </button>
        </form>
        <p className="text-center text-sm">
          Already have an account? <Link to="/login" className="text-blue-600">Sign In</Link>
        </p>
      </div>
    </div>
  )
}