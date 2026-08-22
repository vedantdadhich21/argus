export default function AttackChain({ steps = [] }) {
  if (!steps?.length) return (
    <p className="text-sm" style={{ color: '#3f3f46' }}>No attack chain data.</p>
  )

  return (
    <div className="relative pl-8">
      {/* Vertical connector line */}
      <div className="absolute left-3 top-4 bottom-4 w-px" style={{ background: 'rgba(255,255,255,0.06)' }} />

      <div className="flex flex-col gap-4">
        {steps.map((step) => (
          <div key={step.step} className="relative flex gap-5">
            {/* Step number — plain monospace, no red bubble */}
            <div className="absolute -left-8 flex h-6 w-6 flex-shrink-0 items-center justify-center">
              <span className="font-mono text-xs font-semibold" style={{ color: '#52525b' }}>
                {String(step.step).padStart(2, '0')}
              </span>
            </div>

            {/* Content card */}
            <div className="flex-1 rounded-lg p-4"
              style={{ background: '#111113', border: '1px solid rgba(255,255,255,0.07)' }}>
              <h4 className="text-sm font-semibold text-white mb-1.5">{step.title}</h4>
              <p className="text-sm leading-relaxed" style={{ color: '#71717a' }}>{step.detail}</p>
              {step.evidence?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {step.evidence.map((e) => (
                    <span key={e} className="font-mono text-xs px-2 py-0.5 rounded"
                      style={{ color: '#a1a1aa', background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
                      {e}
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}


