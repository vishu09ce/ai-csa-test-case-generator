import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import DocumentCard from '../DocumentCard'

vi.mock('../../services/api', () => ({
  downloadFile: (projectId, fileName) => `/api/projects/${projectId}/files/${fileName}`,
}))

const baseDoc = {
  doc_code: 'SAP',
  status: 'AI_COMPLETE',
  has_ai_pdf: false,
  has_word: false,
  has_hitl_pdf: false,
}

describe('DocumentCard', () => {
  it('renders document code and full label', () => {
    render(<DocumentCard doc={baseDoc} projectId="proj-1" onHitlUpload={vi.fn()} />)
    expect(screen.getByText('SAP')).toBeInTheDocument()
    expect(screen.getByText('Software Assurance Plan')).toBeInTheDocument()
  })

  it('shows AI PDF download link when has_ai_pdf is true', () => {
    render(<DocumentCard doc={{ ...baseDoc, has_ai_pdf: true }} projectId="proj-1" onHitlUpload={vi.fn()} />)
    expect(screen.getByText('AI PDF')).toBeInTheDocument()
  })

  it('shows Word download link when has_word is true', () => {
    render(<DocumentCard doc={{ ...baseDoc, has_word: true }} projectId="proj-1" onHitlUpload={vi.fn()} />)
    expect(screen.getByText('Download Word')).toBeInTheDocument()
  })

  it('shows Upload HITL button when has_word and no hitl yet', () => {
    render(<DocumentCard doc={{ ...baseDoc, has_word: true, has_hitl_pdf: false }} projectId="proj-1" onHitlUpload={vi.fn()} />)
    expect(screen.getByText('Upload HITL')).toBeInTheDocument()
  })

  it('hides Upload HITL when HITL already uploaded', () => {
    render(<DocumentCard doc={{ ...baseDoc, has_word: true, has_hitl_pdf: true }} projectId="proj-1" onHitlUpload={vi.fn()} />)
    expect(screen.queryByText('Upload HITL')).not.toBeInTheDocument()
  })

  it('shows HITL PDF link when has_hitl_pdf is true', () => {
    render(<DocumentCard doc={{ ...baseDoc, has_hitl_pdf: true }} projectId="proj-1" onHitlUpload={vi.fn()} />)
    expect(screen.getByText('HITL PDF')).toBeInTheDocument()
  })

  it('returns null when doc is null', () => {
    const { container } = render(<DocumentCard doc={null} projectId="proj-1" onHitlUpload={vi.fn()} />)
    expect(container.firstChild).toBeNull()
  })

  it('displays status badge', () => {
    render(<DocumentCard doc={{ ...baseDoc, status: 'GENERATING' }} projectId="proj-1" onHitlUpload={vi.fn()} />)
    expect(screen.getByText('GENERATING')).toBeInTheDocument()
  })
})
