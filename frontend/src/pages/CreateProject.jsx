import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createProject } from '../services/api'

const SYSTEM_TYPES = ['MES', 'LIMS', 'QMS', 'CAPA', 'DMS', 'LMS', 'ERP']

const SYSTEM_DESCRIPTIONS = {
  MES: 'Manufacturing Execution System',
  LIMS: 'Laboratory Information Management System',
  QMS: 'Quality Management System',
  CAPA: 'Corrective and Preventive Action System',
  DMS: 'Document Management System',
  LMS: 'Learning Management System',
  ERP: 'Enterprise Resource Planning',
}

export default function CreateProject() {
  const [name, setName] = useState('')
  const [systemType, setSystemType] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!name.trim() || !systemType) return
    setLoading(true)
    setError('')
    try {
      const res = await createProject(name.trim(), systemType)
      navigate(`/projects/${res.data.id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to create project.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-lg mx-auto px-4 py-8">
      <button onClick={() => navigate('/')} className="text-sm text-gray-500 hover:text-gray-700 mb-6 flex items-center gap-1">
        ← Back to Dashboard
      </button>
      <h1 className="text-xl font-bold text-gray-900 mb-6">Create New Project</h1>

      <form onSubmit={handleSubmit} className="space-y-5">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Project Name</label>
          <input
            type="text"
            value={name}
            onChange={e => setName(e.target.value)}
            placeholder="e.g. LIMS Validation 2026"
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Industry</label>
          <input
            type="text"
            value="Life Sciences"
            disabled
            className="w-full border rounded-lg px-3 py-2 text-sm bg-gray-50 text-gray-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">System Type</label>
          <select
            value={systemType}
            onChange={e => setSystemType(e.target.value)}
            className="w-full border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            required
          >
            <option value="">Select a system type...</option>
            {SYSTEM_TYPES.map(t => (
              <option key={t} value={t}>{t} — {SYSTEM_DESCRIPTIONS[t]}</option>
            ))}
          </select>
        </div>

        {error && <p className="text-sm text-red-500">{error}</p>}

        <button
          type="submit"
          disabled={loading || !name.trim() || !systemType}
          className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white font-medium py-2 rounded-lg text-sm transition-colors"
        >
          {loading ? 'Creating...' : 'Create Project'}
        </button>
      </form>
    </div>
  )
}
