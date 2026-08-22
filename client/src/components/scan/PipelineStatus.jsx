import { CheckCircle2, Loader2, Circle, AlertTriangle } from 'lucide-react'

const STAGES = [
  { key: 'queued',           label: 'Queued',                 hint: 'Waiting in queue' },
  { key: 'static_analysis', label: 'Static Analysis',         hint: 'Parsing manifest & permissions' },
  { key: 'decompiling',     label: 'Decompiling',             hint: 'Running jadx bytecode decompiler' },
  { key: 'ai_analysis',     label: 'AI Behavioral Analysis',  hint: 'LLM reconstructing attack chain' },
  { key: 'completed',       label: 'Complete',                hint: 'Analysis complete — report ready' },
]

// Map all 8 backend pipeline statuses to the 5 UI display stages
const STAGE_INDEX_MAP = {
  'queued': 0,
  'static_analysis': 1,
  'decompiling': 2,
  'pattern_scanning': 2,
  'ioc_extraction': 2,
  'scoring': 3,
  'ai_analysis': 3,
  'building_report': 3,
  'completed': 5, // All 5 steps completed
  'failed': -1,
}

export default function PipelineStatus({ status, progressHint }) {
  const isCompleted = status === 'completed'
  const isFailed = status === 'failed'
  const currentIdx = STAGE_INDEX_MAP[status] ?? (isCompleted ? 5 : 0)

  return (
    <div className="flex flex-col gap-2">
      {status && (
        <p className={`text-xs ${isCompleted ? 'text-green-400' : isFailed ? 'text-red-400' : 'text-slate-400 animate-pulse'} mb-1`}>
          {isCompleted
            ? '✓ Analysis complete — Threat report generated'
            : isFailed
            ? '✕ Analysis failed'
            : (progressHint || STAGES[Math.min(currentIdx, STAGES.length - 1)]?.hint)}
        </p>
      )}
      <div className="flex items-center gap-0">
        {STAGES.map((stage, i) => {
          const done    = isCompleted || currentIdx > i
          const active  = !isCompleted && !isFailed && currentIdx === i
          const pending = !isCompleted && currentIdx < i

          return (
            <div key={stage.key} className="flex items-center">
              {/* Step */}
              <div className="flex flex-col items-center gap-1 min-w-[72px]">
                <div className={`flex h-7 w-7 items-center justify-center rounded-full border-2 transition-all duration-500
                  ${done    ? 'border-green-500 bg-green-500/20 text-green-400' : ''}
                  ${active  ? 'border-red-400  bg-red-500/20 animate-pulse' : ''}
                  ${pending ? 'border-white/10 bg-transparent text-white/20' : ''}
                  ${isFailed && active ? 'border-red-500 bg-red-500/20 text-red-400' : ''}
                `}>
                  {done   && <CheckCircle2 className="h-4 w-4 text-green-400" />}
                  {active && !isFailed && <Loader2 className="h-4 w-4 text-red-400 animate-spin" />}
                  {isFailed && active && <AlertTriangle className="h-4 w-4 text-red-400" />}
                  {pending && <Circle className="h-4 w-4 text-white/20" />}
                </div>
                <span className={`text-[10px] text-center leading-tight transition-colors
                  ${done   ? 'text-green-400 font-medium' : ''}
                  ${active ? 'text-red-400 font-semibold' : ''}
                  ${pending ? 'text-slate-600' : ''}
                `}>{stage.label}</span>
              </div>

              {/* Connector */}
              {i < STAGES.length - 1 && (
                <div className={`h-px w-6 flex-shrink-0 transition-all duration-700 -mt-5
                  ${done ? 'bg-green-500/50' : 'bg-white/10'}`}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
