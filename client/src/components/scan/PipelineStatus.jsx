import { Loader2 } from 'lucide-react'

const STAGES = [
  { key: 'queued',           label: 'Queued' },
  { key: 'static_analysis', label: 'Static analysis' },
  { key: 'decompiling',     label: 'Decompiling bytecode' },
  { key: 'ai_analysis',     label: 'AI behavioral analysis' },
  { key: 'completed',       label: 'Complete' },
]

const STAGE_INDEX_MAP = {
  'queued': 0,
  'static_analysis': 1,
  'decompiling': 2,
  'pattern_scanning': 2,
  'ioc_extraction': 2,
  'scoring': 3,
  'ai_analysis': 3,
  'building_report': 3,
  'completed': 5,
  'failed': -1,
}

export default function PipelineStatus({ status, progressHint }) {
  const isCompleted = status === 'completed'
  const isFailed    = status === 'failed'
  const currentIdx  = STAGE_INDEX_MAP[status] ?? (isCompleted ? 5 : 0)

  if (isCompleted || isFailed) return null

  return (
    <div className="flex flex-col gap-3">
      {progressHint && (
        <div className="flex items-center gap-2">
          <Loader2 className="h-3.5 w-3.5 animate-spin flex-shrink-0" style={{ color: '#52525b' }} />
          <p className="text-xs" style={{ color: '#71717a' }}>{progressHint}</p>
        </div>
      )}
      <div className="flex flex-col gap-1.5">
        {STAGES.map((stage, i) => {
          const done    = isCompleted || currentIdx > i
          const active  = !isCompleted && !isFailed && currentIdx === i
          const pending = !isCompleted && currentIdx < i
          return (
            <div key={stage.key} className="flex items-center gap-2.5">
              <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{
                background: done ? '#22c55e' : active ? '#fafafa' : '#27272a'
              }} />
              <span className="text-xs" style={{
                color: done ? '#52525b' : active ? '#fafafa' : '#27272a',
                fontWeight: active ? 500 : 400,
              }}>
                {stage.label}
                {done && ' ✓'}
              </span>
            </div>
          )
        })}
      </div>
    </div>
  )
}
