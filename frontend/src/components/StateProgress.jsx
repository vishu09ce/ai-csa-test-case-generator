const STATES = [
  'DRAFT', 'SAP_REVIEW', 'PRA_REVIEW', 'RTM_REVIEW',
  'PROTOCOL_REVIEW', 'EXECUTION', 'SUMMARY_REVIEW', 'COMPLETE'
]

const STATE_LABELS = {
  DRAFT: 'Draft',
  SAP_REVIEW: 'SAP Review',
  PRA_REVIEW: 'PRA Review',
  RTM_REVIEW: 'RTM Review',
  PROTOCOL_REVIEW: 'Protocol Review',
  EXECUTION: 'Execution',
  SUMMARY_REVIEW: 'Summary Review',
  COMPLETE: 'Complete',
}

export default function StateProgress({ currentState }) {
  const currentIndex = STATES.indexOf(currentState)
  return (
    <div className="flex items-center gap-1 flex-wrap">
      {STATES.map((state, i) => {
        const isDone = i < currentIndex
        const isCurrent = i === currentIndex
        return (
          <div key={state} className="flex items-center gap-1">
            <span className={`text-xs px-2 py-1 rounded-full font-medium
              ${isCurrent ? 'bg-blue-600 text-white' : ''}
              ${isDone ? 'bg-green-100 text-green-700' : ''}
              ${!isCurrent && !isDone ? 'bg-gray-100 text-gray-400' : ''}
            `}>
              {STATE_LABELS[state]}
            </span>
            {i < STATES.length - 1 && (
              <span className="text-gray-300 text-xs">→</span>
            )}
          </div>
        )
      })}
    </div>
  )
}
