import api from './client'

export async function getNearbyDermatologists(lat, lng) {
  // Explicit timeout — Overpass is a public, sometimes-slow API. If it's
  // having a bad day we'd rather fail fast with a clear message than
  // leave the user staring at "Loading..." for minutes.
  const res = await api.get('/derm-locator/nearby', {
    params: { lat, lng },
    timeout: 25000,
  })
  return res.data
}