import { useState, useEffect, useRef } from 'react'
import { useAuth } from '../context/AuthContext'
import { updateMe, deleteMe } from '../api/auth'
import { useNavigate } from 'react-router-dom'

export default function UserProfile() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const [fullName, setFullName] = useState(user?.full_name || '')
  const [email, setEmail] = useState(user?.email || '')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')
  const [messageType, setMessageType] = useState('success') // 'success' | 'error'
  const timeoutRef = useRef(null)

  useEffect(() => {
    return () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current)
    }
  }, [])

  const showMessage = (text, type = 'success') => {
    setMessage(text)
    setMessageType(type)
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => setMessage(''), 5000)
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const updatedUser = await updateMe({ full_name: fullName, email })
      // Reflect whatever the server actually saved, in case it
      // normalized/trimmed the values — falls back to what we sent.
      setFullName(updatedUser?.full_name ?? fullName)
      setEmail(updatedUser?.email ?? email)
      showMessage('Profile updated successfully', 'success')
    } catch (err) {
      showMessage(err.response?.data?.detail || 'Update failed', 'error')
    } finally {
      setLoading(false)
    }
  }

  const handleDelete = async () => {
    if (window.confirm('Are you sure? This action is irreversible.')) {
      try {
        await deleteMe()
        logout()
        navigate('/login')
      } catch (err) {
        alert(err.response?.data?.detail || 'Deletion failed')
      }
    }
  }

  return (
    <div className="max-w-md mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Profile</h1>
      <form onSubmit={handleUpdate} className="space-y-4">
        <div>
          <label className="block text-sm font-medium">Full Name</label>
          <input
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <div>
          <label className="block text-sm font-medium">Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full p-2 border rounded"
            required
          />
        </div>
        <button
          type="submit"
          disabled={loading}
          className="w-full bg-blue-600 text-white p-2 rounded hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Updating...' : 'Update Profile'}
        </button>
        {message && (
          <p className={`text-sm ${messageType === 'success' ? 'text-green-600' : 'text-red-600'}`}>
            {message}
          </p>
        )}
      </form>

      <hr className="my-6" />

      <button
        onClick={handleDelete}
        className="w-full bg-red-600 text-white p-2 rounded hover:bg-red-700"
      >
        Delete Account
      </button>
    </div>
  )
}