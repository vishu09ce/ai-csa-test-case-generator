import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { listProjects } from '../services/api'
import StateProgress from '../components/StateProgress'

export default function Dashboard() {
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    listProjects()
      .then(res => setProjects(res.data))
      .catch(() => setError('Failed to load projects.'))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">CSA Test Case Generator</h1>
          <p className="text-sm text-gray-500 mt-1">AI-Powered FDA CSA Validation Document Generator</p>
        </div>
        <button
          onClick={() => navigate('/create')}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
        >
          + New Project
        </button>
      </div>

      {loading && <p className="text-gray-500">Loading projects...</p>}
      {error && <p className="text-red-500">{error}</p>}

      {!loading && projects.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-lg">No projects yet.</p>
          <p className="text-sm mt-1">Click "New Project" to get started.</p>
        </div>
      )}

      <div className="space-y-4">
        {projects.map(project => (
          <div
            key={project.id}
            className="bg-white border rounded-lg p-5 shadow-sm cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => navigate(`/projects/${project.id}`)}
          >
            <div className="flex justify-between items-start mb-3">
              <div>
                <h2 className="font-semibold text-gray-900">{project.name}</h2>
                <p className="text-xs text-gray-500 mt-0.5">{project.id} · {project.system_type} · {project.industry}</p>
              </div>
              <span className={`text-xs px-2 py-1 rounded-full font-medium
                ${project.state === 'COMPLETE' ? 'bg-green-100 text-green-700' : 'bg-blue-50 text-blue-700'}
              `}>
                {project.state.replace('_', ' ')}
              </span>
            </div>
            <StateProgress currentState={project.state} />
            <p className="text-xs text-gray-400 mt-3">
              Created {new Date(project.created_at).toLocaleDateString()}
              {project.updated_at && ` · Updated ${new Date(project.updated_at).toLocaleDateString()}`}
            </p>
          </div>
        ))}
      </div>
    </div>
  )
}
