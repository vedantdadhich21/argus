import { CheckCircle2, Loader2, Circle } from 'lucide-react'

const STAGES = [
  { key: 'queued',           label: 'Queued',                 hint: 'Waiting in queue' },
  { key: 'static_analysis', label: 'Static Analysis',         hint: 'Parsing manifest & permissions' },
  { key: 'decompiling',     label: 'Decompiling',             hint: 'Running jadx bytecode decompiler' },
  { key: 'ai_analysis',     label: 'AI Behavioral Analysis',  hint: 'LLM reconstructing attack chain' },
  { key: 'completed',       label: 'Complete',                hint: 'Report ready' },
]

const ORDER = STAGES.map(s => s.key)

export default function PipelineStatus({ status, progressHint }) {
  const currentIdx = ORDER.indexOf(status)

  return (
    <div className="flex flex-col gap-2">
      {status && (
        <p className="text-xs text-slate-400 mb-1 animate-pulse">
          {progressHint || STAGES.find(s => s.key === status)?.hint}
        </p>
      )}
      <div className="flex items-center gap-0">
        {STAGES.map((stage, i) => {
          const done    = currentIdx > i
          const active  = currentIdx === i
          const pending = currentIdx < i

          return (
            <div key={stage.key} className="flex items-center">
              {/* Step */}
              <div className={`flex flex-col items-center gap-1 min-w-[72px]`}>
                <div className={`flex h-7 w-7 items-center justify-center rounded-full border-2 transition-all duration-500
                  ${done    ? 'border-green-500 bg-green-500/20' : ''}
                  ${active  ? 'border-red-400  bg-red-500/20 animate-pulse' : ''}
                  ${pending ? 'border-white/10 bg-transparent' : ''}
                `}>
                  {done   && <CheckCircle2 className="h-4 w-4 text-green-400" />}
                  {active && <Loader2      className="h-4 w-4 text-red-400 animate-spin" />}
                  {pending && <Circle      className="h-4 w-4 text-white/20" />}
                </div>
                <span className={`text-[10px] text-center leading-tight transition-colors
                  ${done   ? 'text-green-400' : ''}
                  ${active ? 'text-red-400 font-semibold' : ''}
                  ${pending ? 'text-slate-600' : ''}
                `}>{stage.label}</span>
              </div>

              {/* Connector */}
              {i < STAGES.length - 1 && (
                <div className={`h-px w-6 flex-shrink-0 transition-all duration-700 -mt-5
                  ${currentIdx > i ? 'bg-green-500/50' : 'bg-white/10'}`}
                />
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
