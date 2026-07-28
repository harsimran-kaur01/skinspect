export function getErrorMessage(error) {
  if (!error?.response?.data) return 'An unexpected error occurred'
  
  const detail = error.response.data.detail
  if (Array.isArray(detail)) {
    return detail.map(d => d.msg || JSON.stringify(d)).join('. ')
  }
  if (typeof detail === 'string') return detail
  if (typeof detail === 'object' && detail !== null) {
    return JSON.stringify(detail)
  }
  return 'An unexpected error occurred'
}