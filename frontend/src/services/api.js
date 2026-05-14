import axios from 'axios'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || ''

const api = axios.create({ baseURL: `${BACKEND_URL}/api` })

export const createProject = (name, systemType) =>
  api.post('/projects', { name, system_type: systemType })

export const listProjects = () =>
  api.get('/projects')

export const getProject = (id) =>
  api.get(`/projects/${id}`)

export const updateProject = (id, data) =>
  api.patch(`/projects/${id}`, data)

export const uploadSourceDocument = (projectId, docType, file) => {
  const form = new FormData()
  form.append('doc_type', docType)
  form.append('file', file)
  return api.post(`/projects/${projectId}/upload/source`, form)
}

export const uploadHitlDocument = (projectId, docCode, file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post(`/projects/${projectId}/upload/hitl/${docCode}`, form)
}

export const startGeneration = (projectId) =>
  api.post(`/projects/${projectId}/start`)

export const submitForReview = (projectId, docCode) =>
  api.post(`/projects/${projectId}/submit/${docCode}`)

export const getProjectStatus = (projectId) =>
  api.get(`/projects/${projectId}/status`)

export const downloadFile = (projectId, fileName) =>
  `${api.defaults.baseURL}/projects/${projectId}/files/${fileName}`

export const downloadPackage = (projectId) =>
  `${api.defaults.baseURL}/projects/${projectId}/package`
