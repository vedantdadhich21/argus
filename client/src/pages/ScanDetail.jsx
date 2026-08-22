import { useParams } from 'react-router-dom'
import { useScan } from '../hooks/useScan'
import VerdictCard from '../components/scan/VerdictCard'
import PipelineStatus from '../components/scan/PipelineStatus'
import ScoreBreakdown from '../components/scan/ScoreBreakdown'
import PermissionTable from '../components/scan/PermissionTable'
import AiFindings from '../components/scan/AiFindings'
import IocTable from '../components/scan/IocTable'
import { Download, Loader2, AlertCircle } from 'lucide-react'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

const TABS = ['Overview', 'Findings', 'AI Analysis', 'IOCs', 'Report']

const WORKING = ['queued', 'static_analysis', 'decompiling', 'ai_analysis']

export default function ScanDetail() {
  const { id } = useParams()
  const { data: scan, isLoading, isError } = useScan(id)
  const [tab, setTab] = useState('Overview')

  if (isLoading || (scan && WORKING.includes(scan.status))) {
    return (
      <div className="min-h-screen bg-slate-950 pt-20">
        <div className="mx-auto max-w-5xl px-6 py-16">
          {/* Live pipeline view */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.02] p-8">
            <div className="flex items-center gap-3 mb-8">
              <Loader2 className="h-5 w-5 animate-spin text-red-400" />
              <h1 className="text-lg font-bold text-white">Scanning in progress…</h1>
            </div>
            <PipelineStatus status={scan?.status ?? 'queued'} progressHint={scan?.progress_hint} />
          </div>
        </div>
      </div>
    )
  }

  if (isError || !scan) {
    return (
      <div className="min-h-screen bg-slate-950 pt-20 flex items-center justify-center">
        <div className="flex items-center gap-3 text-slate-400">
          <AlertCircle className="h-6 w-6 text-red-400" />
          <p>Scan not found or failed to load. Check the scan ID.</p>
        </div>
      </div>
    )
  }

  const downloadReport = () => {
    const blob = new Blob([scan.report_markdown ?? '# No report'], { type: 'text/markdown' })
    const url  = URL.createObjectURL(blob)
    const a    = Object.assign(document.createElement('a'), { href: url, download: `sentinel-report-${id}.md` })
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-slate-950 pt-20">
      <div className="mx-auto max-w-5xl px-6 py-10">
        {/* Verdict card */}
        <VerdictCard scan={scan} />

        {/* AI Degradation Alert Banner if applicable */}
        {scan.ai_status === 'unavailable' && (
          <div className="mt-4 rounded-xl border border-amber-500/20 bg-amber-500/10 p-4 flex items-start gap-3 text-xs text-amber-300">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5 text-amber-400" />
            <div>
              <span className="font-semibold">AI Behavioral Analysis Offline:</span> The Generative AI layer is currently operating in degraded mode. The threat score, triggered rules, and IOCs above are fully verified via our deterministic static and bytecode analysis engine.
            </div>
          </div>
        )}

        {/* Tabs */}
        <div className="mt-8 flex gap-1 border-b border-white/5">
          {TABS.map(t => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium transition-all border-b-2 -mb-px ${
                tab === t
                  ? 'border-red-400 text-white'
                  : 'border-transparent text-slate-500 hover:text-slate-300'
              }`}
            >
              {t}
            </button>
          ))}

          {/* Download btn */}
          <button
            onClick={downloadReport}
            className="ml-auto flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-400 hover:text-white hover:border-white/20 transition-all mb-1"
          >
            <Download className="h-3.5 w-3.5" />
            Download .md
          </button>
        </div>

        {/* Tab content */}
        <div className="mt-8">
          {tab === 'Overview' && (
            <div className="flex flex-col gap-6">
              <PipelineStatus status={scan.status} progressHint={scan.progress_hint} />
              {/* App metadata */}
              {scan.app_metadata && (
                <div className="rounded-xl border border-white/5 bg-white/[0.02] p-5">
                  <h3 className="text-sm font-semibold text-white mb-3">App Metadata</h3>
                  <dl className="grid grid-cols-2 gap-3 sm:grid-cols-3 text-xs">
                    {Object.entries(scan.app_metadata).map(([k, v]) => (
                      <div key={k}>
                        <dt className="text-slate-500 mb-0.5">{k.replace(/_/g,' ')}</dt>
                        <dd className="font-mono text-slate-300 break-all">{String(v)}</dd>
                      </div>
                    ))}
                  </dl>
                </div>
              )}
            </div>
          )}

          {tab === 'Findings' && (
            <div className="flex flex-col gap-6">
              <ScoreBreakdown triggers={scan.triggers} />
              <PermissionTable permissions={scan.permissions} />
            </div>
          )}

          {tab === 'AI Analysis' && (
            <AiFindings scan={scan} />
          )}

          {tab === 'IOCs' && (
            <IocTable iocs={scan.iocs} />
          )}

          {tab === 'Report' && (
            <div className="rounded-xl border border-white/5 bg-white/[0.02] p-6 prose prose-invert prose-sm max-w-none">
              <ReactMarkdown>{scan.report_markdown ?? '*No report generated yet.*'}</ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
