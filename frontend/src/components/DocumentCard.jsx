import { downloadFile } from '../services/api'

const STATUS_STYLES = {
  NOT_STARTED: 'bg-gray-100 text-gray-500',
  GENERATING: 'bg-yellow-100 text-yellow-700 animate-pulse',
  AI_COMPLETE: 'bg-blue-100 text-blue-700',
  IN_REVIEW: 'bg-orange-100 text-orange-700',
  HITL_COMPLETE: 'bg-green-100 text-green-700',
}

const DOC_LABELS = {
  SAP: 'Software Assurance Plan',
  PRA: 'Process Risk Assessment',
  RTM: 'Requirements Traceability Matrix',
  STP: 'Scripted Test Protocol',
  UTR: 'Unscripted Test Record',
  ASR: 'Assurance Summary Report',
}

export default function DocumentCard({ doc, projectId, onHitlUpload }) {
  if (!doc) return null
  const { doc_code, status, has_ai_pdf, has_word, has_hitl_pdf } = doc

  return (
    <div className="border rounded-lg p-4 bg-white shadow-sm">
      <div className="flex justify-between items-start mb-3">
        <div>
          <p className="font-semibold text-gray-800">{doc_code}</p>
          <p className="text-xs text-gray-500">{DOC_LABELS[doc_code]}</p>
        </div>
        <span className={`text-xs px-2 py-1 rounded-full font-medium ${STATUS_STYLES[status] || STATUS_STYLES.NOT_STARTED}`}>
          {status?.replace('_', ' ')}
        </span>
      </div>

      <div className="flex flex-wrap gap-2">
        {has_ai_pdf && (
          <a
            href={downloadFile(projectId, `${doc_code}-AI-${projectId}.pdf`)}
            target="_blank"
            rel="noreferrer"
            className="text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 px-3 py-1 rounded"
          >
            AI PDF
          </a>
        )}
        {has_word && (
          <a
            href={downloadFile(projectId, `${doc_code}-REVIEW-${projectId}.docx`)}
            className="text-xs bg-blue-50 hover:bg-blue-100 text-blue-700 px-3 py-1 rounded"
          >
            Download Word
          </a>
        )}
        {has_hitl_pdf && (
          <a
            href={downloadFile(projectId, `${doc_code}-HITL-${projectId}.pdf`)}
            target="_blank"
            rel="noreferrer"
            className="text-xs bg-green-50 hover:bg-green-100 text-green-700 px-3 py-1 rounded"
          >
            HITL PDF
          </a>
        )}
        {has_word && !has_hitl_pdf && (
          <label className="text-xs bg-orange-50 hover:bg-orange-100 text-orange-700 px-3 py-1 rounded cursor-pointer">
            Upload HITL
            <input
              type="file"
              accept=".docx"
              className="hidden"
              onChange={(e) => onHitlUpload(doc_code, e.target.files[0])}
            />
          </label>
        )}
      </div>
    </div>
  )
}
