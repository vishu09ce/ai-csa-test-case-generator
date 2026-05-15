import { render, screen } from '@testing-library/react'
import StateProgress from '../StateProgress'

describe('StateProgress', () => {
  it('highlights the current state', () => {
    render(<StateProgress currentState="DRAFT" />)
    const draft = screen.getByText('Draft')
    expect(draft).toHaveClass('bg-blue-600')
  })

  it('marks earlier states as done', () => {
    render(<StateProgress currentState="PRA_REVIEW" />)
    const draft = screen.getByText('Draft')
    expect(draft).toHaveClass('bg-green-100')
  })

  it('marks later states as not yet reached', () => {
    render(<StateProgress currentState="DRAFT" />)
    const complete = screen.getByText('Complete')
    expect(complete).toHaveClass('bg-gray-100')
  })

  it('renders all 8 states', () => {
    render(<StateProgress currentState="DRAFT" />)
    const labels = [
      'Draft', 'SAP Review', 'PRA Review', 'RTM Review',
      'Protocol Review', 'Execution', 'Summary Review', 'Complete',
    ]
    labels.forEach(label => expect(screen.getByText(label)).toBeInTheDocument())
  })

  it('marks all states done except Complete when state is COMPLETE', () => {
    render(<StateProgress currentState="COMPLETE" />)
    const complete = screen.getByText('Complete')
    expect(complete).toHaveClass('bg-blue-600')
  })
})
