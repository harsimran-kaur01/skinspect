import { createContext, useContext, useState, useEffect } from 'react'
import { getMe, login as apiLogin, register as apiRegister } from '../api/auth'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      getMe()
        .then(user => setUser(user))
        .catch(() => {
          localStorage.removeItem('token')
          setToken(null)
        })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token])

  const login = async (email, password) => {
    try {
      const data = await apiLogin(email, password)

      const { access_token, token_type } = data.token
      const fullToken = `${token_type} ${access_token}`

      localStorage.setItem('token', fullToken)
      setToken(fullToken)

      const userData = await getMe()
      setUser(userData)

      return userData
    } catch (error) {
      // Re-throw so Login.jsx can display the error
      throw error
    }
  }

  const register = async (email, password, full_name) => {
    try {
      const data = await apiRegister(email, password, full_name)

      const { access_token, token_type } = data.token
      const fullToken = `${token_type} ${access_token}`

      localStorage.setItem('token', fullToken)
      setToken(fullToken)

      const userData = await getMe()
      setUser(userData)

      return userData
    } catch (error) {
      // Re-throw so Register.jsx can display the error
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{ user, token, loading, login, register, logout }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  return useContext(AuthContext)
}