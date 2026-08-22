export default function AttackChain({ steps = [] }) {
  return (
    <div className="relative pl-6">
      {/* Vertical line */}
      <div className="absolute left-3 top-3 bottom-3 w-px bg-gradient-to-b from-red-500/50 to-transparent" />

      <div className="flex flex-col gap-4">
        {steps.map((step) => (
          <div key={step.step} className="relative flex gap-4">
            {/* Step number bubble */}
            <div className="absolute -left-6 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-red-500 text-xs font-bold text-white shadow-lg shadow-red-500/30">
              {step.step}
            </div>

            {/* Content */}
            <div className="ml-2 rounded-xl border border-white/5 bg-white/[0.02] p-4 flex-1 hover:border-white/10 transition-colors">
              <div className="flex items-start justify-between gap-2 mb-1">
                <h4 className="text-sm font-bold text-white">{step.title}</h4>
              </div>
              <p className="text-sm text-slate-400 leading-relaxed">{step.detail}</p>
              {step.evidence?.length > 0 && (
                <div className="mt-3 flex flex-wrap gap-1.5">
                  {step.evidence.map((e) => (
                    <span key={e} className="rounded-md border border-orange-500/20 bg-orange-500/10 px-2 py-0.5 font-mono text-xs text-orange-400">
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
