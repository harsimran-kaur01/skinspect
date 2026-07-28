import api from './client'

export async function login(email, password) {
  const res = await api.post('/auth/login', { email, password })
  return res.data
}

export async function register(email, password, full_name) {
  const res = await api.post('/auth/register', { email, password, full_name })
  return res.data
}

export async function getMe() {
  const res = await api.get('/auth/me')
  return res.data
}

export async function updateMe(data) {
  const res = await api.put('/auth/me', data)
  return res.data
}

export async function deleteMe() {
  await api.delete('/auth/me')
}

export async function verifyEmail(token) {
  const res = await api.post('/auth/verify-email', { token })
  return res.data
}

export async function resendVerification() {
  const res = await api.post('/auth/resend-verification')
  return res.data
}