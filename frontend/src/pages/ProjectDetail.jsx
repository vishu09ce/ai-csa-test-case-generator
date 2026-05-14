import { useEffect, useState, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  getProjectStatus, uploadSourceDocument, uploadHitlDocument,
  startGeneration, submitForReview, downloadPackage
} from '../services/api'
import StateProgress from '../components/StateProgress'
import DocumentCard from '../components/DocumentCard'
import UploadZone from '../components/UploadZone'

const DOC_CODES = ['SAP', 'PRA', 'RTM', 'STP', 'UTR', 'ASR']

const SUBMIT_DOC_MAP = {
  SAP_REVIEW: 'SAP',
  PRA_REVIEW: 'PRA',
  RTM_REVIEW: 'RTM',
  PROTOCOL_REVIEW: 'STP',
  EXECUTION: 'STP',
  SUMMARY_REVIEW: 'ASR',
}

export default function ProjectDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState(null)
  const [ursFile, setUrsFile] = useState(null)
  const [frsFile, setFrsFile] = useState(null)
  const [brdFile, setBrdFile] = useState(null)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const fetchStatus = useCallback(() => {
    getProjectStatus(id)
      .then(res => setStatus(res.data))
      .catch(() => setError('Failed to load project status.'))
  }, [id])

  useEffect(() => {
    fetchStatus()
    const interval = setInterval(fetchStatus, 5000)
    return () => clearInterval(interval)
  }, [fetchStatus])

  const handleSourceUpload = async () => {
    if (!ursFile || !frsFile) return setError('URS and FRS are required.')
    setLoading(true); setError(''); setMessage('')
    try {
      await uploadSourceDocument(id, 'URS', ursFile)
      await uploadSourceDocument(id, 'FRS', frsFile)
      if (brdFile) await uploadSourceDocument(id, 'BRD', brdFile)
      setMessage('Documents uploaded successfully.')
      fetchStatus()
    } catch (err) {
      setError(err.response?.data?.detail || 'Upload failed.')
    } finally {
      setLoading(false)
    }
  }

  const handleStartGeneration = async () => {
    setLoading(true); setError(''); setMessage('')
    try {
      await startGeneration(id)
      setMessage('SAP generation started.')
      fetchStatus()
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start generation.')
    } finally {
      setLoading(false)
    }
  }

  const handleHitlUpload = async (docCode, file) => {
    setError(''); setMessage('')
    try {
      await uploadHitlDocument(id, docCode, file)
      setMessage(`${docCode} HITL document uploaded.`)
      fetchStatus()
    } catch (err) {
      setError(err.response?.data?.detail || 'HITL upload failed.')
    }
  }

  const handleSubmit = async () => {
    const docCode = SUBMIT_DOC_MAP[status?.state]
    if (!docCode) return
    setLoading(true); setError(''); setMessage('')
    try {
      const res = await submitForReview(id, docCode)
      setMessage(res.data.message)
      fetchStatus()
    } catch (err) {
      setError(err.response?.data?.detail || 'Submit failed.')
    } finally {
      setLoading(false)
    }
  }

  if (!status) return <div className="p-8 text-gray-500">Loading...</div>

  const { state, documents, active_jobs } = status
  const docMap = Object.fromEntries((documents || []).map(d => [d.doc_code, d]))
  const isGenerating = active_jobs?.some(j => j.status === 'IN_PROGRESS')
  const submitDocCode = SUBMIT_DOC_MAP[state]
  const submitDoc = submitDocCode ? docMap[submitDocCode] : null
  const canSubmit = submitDoc?.has_hitl_pdf && !isGenerating

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <button onClick={() => navigate('/')} className="text-sm text-gray-500 hover:text-gray-700 mb-4">
        ← Back to Dashboard
      </button>

      <div className="bg-white border rounded-lg p-5 shadow-sm mb-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{id}</h1>
            <p className="text-sm text-gray-500 mt-0.5">State: <span className="font-medium text-blue-700">{state}</span></p>
          </div>
          {state === 'COMPLETE' && (
            <a
              href={downloadPackage(id)}
              className="bg-green-600 hover:bg-green-700 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              Download Package
            </a>
          )}
        </div>
        <StateProgress currentState={state} />
      </div>

      {message && <div className="bg-green-50 border border-green-200 text-green-700 text-sm rounded-lg px-4 py-3 mb-4">{message}</div>}
      {error && <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-lg px-4 py-3 mb-4">{error}</div>}
      {isGenerating && <div className="bg-yellow-50 border border-yellow-200 text-yellow-700 text-sm rounded-lg px-4 py-3 mb-4">⏳ Document generation in progress...</div>}

      {state === 'DRAFT' && (
        <div className="bg-white border rounded-lg p-5 shadow-sm mb-6">
          <h2 className="font-semibold text-gray-800 mb-4">Upload Source Documents</h2>
          <div className="space-y-3">
            <UploadZone label="Upload URS (required)" onFile={setUrsFile} file={ursFile} />
            <UploadZone label="Upload FRS (required)" onFile={setFrsFile} file={frsFile} />
            <UploadZone label="Upload BRD (optional)" onFile={setBrdFile} file={brdFile} />
          </div>
          <div className="flex gap-3 mt-4">
            <button
              onClick={handleSourceUpload}
              disabled={loading || !ursFile || !frsFile}
              className="bg-gray-700 hover:bg-gray-800 disabled:bg-gray-300 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              {loading ? 'Uploading...' : 'Upload Documents'}
            </button>
            <button
              onClick={handleStartGeneration}
              disabled={loading || !ursFile || !frsFile}
              className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white text-sm font-medium px-4 py-2 rounded-lg"
            >
              Start Generation
            </button>
          </div>
        </div>
      )}

      <div className="mb-4">
        <h2 className="font-semibold text-gray-800 mb-3">Documents</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {DOC_CODES.map(code => (
            <DocumentCard
              key={code}
              doc={docMap[code] || { doc_code: code, status: 'NOT_STARTED' }}
              projectId={id}
              onHitlUpload={handleHitlUpload}
            />
          ))}
        </div>
      </div>

      {submitDocCode && (
        <div className="bg-white border rounded-lg p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800 mb-2">Submit for Review</h2>
          <p className="text-sm text-gray-500 mb-4">
            Upload the reviewed {submitDocCode} HITL Word file above, then click Submit to advance the project.
          </p>
          <button
            onClick={handleSubmit}
            disabled={!canSubmit || loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 text-white text-sm font-medium px-5 py-2 rounded-lg"
          >
            {loading ? 'Submitting...' : `Submit ${submitDocCode} for Review →`}
          </button>
        </div>
      )}
    </div>
  )
}
