import api from './client'

export async function submitQuestionnaire(data) {
  const res = await api.post('/questionnaire/', data)
  return res.data
}

export async function getQuestionnaire() {
  const res = await api.get('/questionnaire/')
  return res.data
}

export async function checkQuestionnaire() {
  const res = await api.get('/questionnaire/check')
  return res.data
}