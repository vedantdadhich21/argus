import { Brain, ShieldAlert } from 'lucide-react'
import AttackChain from './AttackChain'
import MitreList from './MitreList'

export default function AiFindings({ scan }) {
  const ai = scan?.ai_analysis

  if (scan?.ai_status === 'unavailable') {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-yellow-500/20 bg-yellow-500/10 p-4 text-sm text-yellow-300">
        <ShieldAlert className="h-5 w-5 flex-shrink-0" />
        AI analysis is unavailable for this scan. Verdict is based on the rules engine only.
        The system is still fully operational — only the narrative layer is missing.
      </div>
    )
  }

  if (!ai) return <p className="text-sm text-slate-500">No AI analysis data.</p>

  return (
    <div className="flex flex-col gap-8">
      {/* Behavior summary */}
      <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5">
        <div className="flex items-center gap-2 mb-3">
          <Brain className="h-4 w-4 text-purple-400" />
          <h3 className="text-sm font-semibold text-white">AI Behavior Summary</h3>
          <span className={`ml-auto text-xs font-medium px-2 py-0.5 rounded-full border
            ${ai.confidence === 'high'   ? 'text-red-400 border-red-500/20 bg-red-500/10' :
              ai.confidence === 'medium' ? 'text-yellow-400 border-yellow-500/20 bg-yellow-500/10' :
                                          'text-slate-400 border-white/10 bg-white/5'}
          `}>
            {ai.confidence} confidence
          </span>
        </div>
        <p className="text-sm text-slate-300 leading-relaxed">{ai.behavior_summary}</p>
      </div>

      {/* Attack chain */}
      <div>
        <h3 className="text-sm font-semibold text-white mb-4">Attack Chain</h3>
        <AttackChain steps={ai.attack_chain} />
      </div>

      {/* Recommendations */}
      {ai.recommendations?.length > 0 && (
        <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5">
          <h3 className="text-sm font-semibold text-white mb-3">Recommended Actions</h3>
          <ul className="flex flex-col gap-2">
            {ai.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-slate-400">
                <span className="mt-0.5 flex-shrink-0 h-4 w-4 rounded-full bg-red-500/20 text-red-400 text-xs flex items-center justify-center font-bold">{i+1}</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* MITRE */}
      <div>
        <h3 className="text-sm font-semibold text-white mb-4">MITRE ATT&CK Mobile Mapping</h3>
        <MitreList techniques={ai.mitre_techniques} />
      </div>
    </div>
  )
}
