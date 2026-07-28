import api from './client'

export async function uploadScan(formData) {
  // Two things matter here:
  // 1. Don't set Content-Type to a static 'multipart/form-data' string —
  //    it needs a boundary parameter that only the browser can generate
  //    (e.g. "multipart/form-data; boundary=----WebKitFormBoundary...").
  // 2. client.js sets 'Content-Type: application/json' as an axios
  //    instance-level default, which applies to EVERY request unless
  //    overridden — including this one. So we have to explicitly unset
  //    it (not omit it) or the JSON default silently wins and the
  //    backend gets a FormData body labeled as application/json.
  const res = await api.post('/scans/upload', formData, {
    headers: { 'Content-Type': undefined },
  })
  return res.data
}

export async function getScanHistory(limit = 10, offset = 0) {
  const res = await api.get('/scans/history', { params: { limit, offset } })
  return res.data
}

export async function getScan(scanId) {
  const res = await api.get(`/scans/${scanId}`)
  return res.data
}