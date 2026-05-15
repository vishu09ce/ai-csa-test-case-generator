import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import UploadZone from '../UploadZone'

describe('UploadZone', () => {
  it('renders label when no file selected', () => {
    render(<UploadZone label="Drop URS here" onFile={vi.fn()} />)
    expect(screen.getByText('Drop URS here')).toBeInTheDocument()
  })

  it('shows accepted file types hint', () => {
    render(<UploadZone label="Drop file" accept=".docx,.pdf" onFile={vi.fn()} />)
    expect(screen.getByText(/\.docx,\.pdf/)).toBeInTheDocument()
  })

  it('displays selected file name', () => {
    const file = new File(['content'], 'urs.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    render(<UploadZone label="Drop URS here" onFile={vi.fn()} file={file} />)
    expect(screen.getByText('urs.docx')).toBeInTheDocument()
  })

  it('calls onFile when a file is selected via input', async () => {
    const onFile = vi.fn()
    render(<UploadZone label="Drop file" onFile={onFile} />)
    const input = document.querySelector('input[type="file"]')
    const file = new File(['content'], 'frs.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    await userEvent.upload(input, file)
    expect(onFile).toHaveBeenCalledWith(file)
  })

  it('calls onFile when a file is dropped', () => {
    const onFile = vi.fn()
    render(<UploadZone label="Drop file" onFile={onFile} />)
    const zone = screen.getByText('Drop file').parentElement
    const file = new File(['content'], 'brd.docx', { type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' })
    fireEvent.drop(zone, { dataTransfer: { files: [file] } })
    expect(onFile).toHaveBeenCalledWith(file)
  })
})
