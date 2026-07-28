import { useState } from 'react'
import { useAuth } from '../../context/AuthContext'
import { Link, useNavigate } from 'react-router-dom'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const { login } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
  e.preventDefault()
  try {
    await login(email, password)
    navigate('/dashboard')
  } catch (err) {
    const detail = err.response?.data?.detail
    if (Array.isArray(detail)) {
      setError(detail.map(d => d.msg || JSON.stringify(d)).join('. '))
    } else if (typeof detail === 'string') {
      setError(detail)
    } else {
      setError('Login failed. Please check your credentials.')
    }
  }
}

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <h2 className="text-3xl font-bold text-center">Sign In</h2>
        <form onSubmit={handleSubmit} className="space-y-6">
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
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full p-3 border rounded"
            required
          />
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button type="submit" className="w-full bg-blue-600 text-white p-3 rounded hover:bg-blue-700">
            Sign In
          </button>
        </form>
        <p className="text-center text-sm">
          Don't have an account? <Link to="/register" className="text-blue-600">Register</Link>
        </p>
      </div>
    </div>
  )
}