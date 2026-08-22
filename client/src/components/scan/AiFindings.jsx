import { Sparkles, ShieldAlert, CheckCircle2 } from 'lucide-react'
import AttackChain from './AttackChain'
import MitreList from './MitreList'

export default function AiFindings({ scan }) {
  const ai = scan?.ai_analysis

  if (scan?.ai_status === 'unavailable') {
    return (
      <div className="flex items-start gap-3.5 rounded-lg p-5 text-sm"
        style={{ background: 'rgba(234,179,8,0.06)', border: '1px solid rgba(234,179,8,0.2)', color: '#fde047' }}>
        <ShieldAlert className="h-5 w-5 flex-shrink-0 mt-0.5" />
        <div className="leading-relaxed">
          <p className="font-semibold text-yellow-300">AI behavioral analysis unavailable</p>
          <p className="text-yellow-400/80 text-xs mt-1">
            Verdict was computed using the deterministic static and bytecode pattern scanning engines. All security rules and IOCs remain fully verified.
          </p>
        </div>
      </div>
    )
  }

  if (!ai) return <p className="text-sm" style={{ color: '#52525b' }}>No AI analysis data available.</p>

  const confidenceColors = {
    high:   { text: '#fafafa', bg: 'rgba(255,255,255,0.08)', border: 'rgba(255,255,255,0.15)' },
    medium: { text: '#a1a1aa', bg: 'rgba(255,255,255,0.04)', border: 'rgba(255,255,255,0.08)' },
    low:    { text: '#71717a', bg: 'transparent', border: 'rgba(255,255,255,0.06)' },
  }
  const confStyle = confidenceColors[ai.confidence?.toLowerCase()] ?? confidenceColors.medium

  return (
    <div className="flex flex-col gap-10">
      {/* Behavior summary */}
      <div className="rounded-lg p-6"
        style={{ background: '#111113', border: '1px solid rgba(255,255,255,0.08)' }}>
        <div className="flex items-center justify-between gap-3 mb-4 pb-3"
          style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
          <div className="flex items-center gap-2.5">
            <Sparkles className="h-4 w-4" style={{ color: '#fafafa' }} />
            <h3 className="text-sm font-semibold text-white tracking-tight">Behavioral Synthesis</h3>
          </div>
          <span className="text-xs font-mono font-medium px-2.5 py-1 rounded"
            style={{ color: confStyle.text, background: confStyle.bg, border: `1px solid ${confStyle.border}` }}>
            {ai.confidence} confidence
          </span>
        </div>
        <p className="text-base text-zinc-300 leading-relaxed font-normal">
          {ai.behavior_summary}
        </p>
      </div>

      {/* Attack chain */}
      <div>
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-white uppercase tracking-wider text-xs" style={{ color: '#a1a1aa' }}>
            Reconstructed Kill Chain
          </h3>
          <span className="text-xs font-mono" style={{ color: '#52525b' }}>
            {ai.attack_chain?.length ?? 0} stages identified
          </span>
        </div>
        <AttackChain steps={ai.attack_chain} />
      </div>

      {/* Recommendations */}
      {ai.recommendations?.length > 0 && (
        <div className="rounded-lg p-6"
          style={{ background: '#111113', border: '1px solid rgba(255,255,255,0.08)' }}>
          <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400 mb-4">
            Incident Response Recommendations
          </h3>
          <ul className="flex flex-col gap-3">
            {ai.recommendations.map((r, i) => (
              <li key={i} className="flex items-start gap-3.5 text-sm text-zinc-300 leading-relaxed">
                <span className="mt-0.5 flex-shrink-0 h-5 w-5 rounded flex items-center justify-center font-mono text-xs font-semibold"
                  style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.08)', color: '#fafafa' }}>
                  {i + 1}
                </span>
                <span>{r}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* MITRE */}
      <div>
        <div className="mb-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
            MITRE ATT&CK® Mobile Mappings
          </h3>
        </div>
        <MitreList techniques={ai.mitre_techniques} />
      </div>
    </div>
  )
}

