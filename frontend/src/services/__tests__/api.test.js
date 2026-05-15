import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'

vi.mock('axios', () => {
  const instance = {
    post: vi.fn(),
    get: vi.fn(),
    patch: vi.fn(),
    defaults: { baseURL: '/api' },
  }
  return { default: { create: vi.fn(() => instance) } }
})

import {
  createProject,
  listProjects,
  getProject,
  updateProject,
  startGeneration,
  submitForReview,
  getProjectStatus,
  downloadFile,
  downloadPackage,
} from '../api'

const mockApi = axios.create()

beforeEach(() => {
  vi.clearAllMocks()
})

describe('api service', () => {
  it('createProject posts correct payload', () => {
    mockApi.post.mockResolvedValue({ data: {} })
    createProject('My Project', 'LIMS')
    expect(mockApi.post).toHaveBeenCalledWith('/projects', { name: 'My Project', system_type: 'LIMS' })
  })

  it('listProjects calls GET /projects', () => {
    mockApi.get.mockResolvedValue({ data: [] })
    listProjects()
    expect(mockApi.get).toHaveBeenCalledWith('/projects')
  })

  it('getProject calls GET /projects/:id', () => {
    mockApi.get.mockResolvedValue({ data: {} })
    getProject('proj-123')
    expect(mockApi.get).toHaveBeenCalledWith('/projects/proj-123')
  })

  it('updateProject calls PATCH /projects/:id', () => {
    mockApi.patch.mockResolvedValue({ data: {} })
    updateProject('proj-123', { name: 'Updated' })
    expect(mockApi.patch).toHaveBeenCalledWith('/projects/proj-123', { name: 'Updated' })
  })

  it('startGeneration posts to /projects/:id/start', () => {
    mockApi.post.mockResolvedValue({ data: {} })
    startGeneration('proj-123')
    expect(mockApi.post).toHaveBeenCalledWith('/projects/proj-123/start')
  })

  it('submitForReview posts to /projects/:id/submit/:docCode', () => {
    mockApi.post.mockResolvedValue({ data: {} })
    submitForReview('proj-123', 'SAP')
    expect(mockApi.post).toHaveBeenCalledWith('/projects/proj-123/submit/SAP')
  })

  it('getProjectStatus calls GET /projects/:id/status', () => {
    mockApi.get.mockResolvedValue({ data: {} })
    getProjectStatus('proj-123')
    expect(mockApi.get).toHaveBeenCalledWith('/projects/proj-123/status')
  })

  it('downloadFile returns a direct URL string', () => {
    const url = downloadFile('proj-123', 'SAP-AI-proj-123.pdf')
    expect(url).toContain('proj-123')
    expect(url).toContain('SAP-AI-proj-123.pdf')
  })

  it('downloadPackage returns a direct URL string', () => {
    const url = downloadPackage('proj-123')
    expect(url).toContain('proj-123')
    expect(url).toContain('package')
  })
})
