import { useParams } from 'react-router-dom'
import { useScan } from '../hooks/useScan'
import VerdictCard from '../components/scan/VerdictCard'
import PipelineStatus from '../components/scan/PipelineStatus'
import ScoreBreakdown from '../components/scan/ScoreBreakdown'
import PermissionTable from '../components/scan/PermissionTable'
import AiFindings from '../components/scan/AiFindings'
import IocTable from '../components/scan/IocTable'
import { Download, Loader2, FileCode, AlertCircle } from 'lucide-react'
import { useState } from 'react'
import ReactMarkdown from 'react-markdown'

const TABS = ['Overview', 'Findings & Heuristics', 'AI Analysis', 'IOCs & Network', 'Full Report']

const WORKING = [
  'queued', 'static_analysis', 'decompiling', 'pattern_scanning',
  'ioc_extraction', 'scoring', 'ai_analysis', 'building_report'
]

export default function ScanDetail() {
  const { id } = useParams()
  const { data: scan, isLoading, isError } = useScan(id)
  const [tab, setTab] = useState('Overview')

  if (isLoading || (scan && WORKING.includes(scan.status))) {
    return (
      <div className="min-h-screen pt-14 pb-20" style={{ background: '#08080a' }}>
        <div className="mx-auto max-w-5xl px-6 sm:px-8 py-20">
          <div className="rounded-xl p-8 max-w-2xl mx-auto"
            style={{ background: '#0d0d10', border: '1px solid rgba(255,255,255,0.08)' }}>
            <div className="flex items-center gap-3 mb-6">
              <Loader2 className="h-5 w-5 animate-spin text-sky-400" />
              <div>
                <h2 className="text-base font-semibold text-white">Threat Analysis In Progress</h2>
                <p className="text-xs text-zinc-500 font-mono mt-0.5">Dissecting DEX bytecode and behavioral graph</p>
              </div>
            </div>
            <PipelineStatus status={scan?.status ?? 'queued'} progressHint={scan?.progress_hint} />
          </div>
        </div>
      </div>
    )
  }

  if (isError || !scan) {
    return (
      <div className="min-h-screen pt-14 flex items-center justify-center" style={{ background: '#08080a' }}>
        <div className="p-8 rounded-xl text-center max-w-md"
          style={{ background: '#0d0d10', border: '1px solid rgba(255,255,255,0.08)' }}>
          <AlertCircle className="h-8 w-8 text-zinc-500 mx-auto mb-3" />
          <h2 className="text-base font-semibold text-white mb-1">Scan Report Not Found</h2>
          <p className="text-xs text-zinc-400">The requested scan ID does not exist or the data has expired.</p>
        </div>
      </div>
    )
  }

  const downloadReport = () => {
    const blob = new Blob([scan.report_markdown ?? '# No report'], { type: 'text/markdown' })
    const url  = URL.createObjectURL(blob)
    const a    = Object.assign(document.createElement('a'), { href: url, download: `argus-threat-report-${id}.md` })
    a.click()
    URL.revokeObjectURL(url)
  }

  const downloadPdf = async () => {
    const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
    window.open(`${API_BASE}/api/scan/${id}/report?format=pdf`, '_blank')
  }

  return (
    <div className="min-h-screen pt-14 pb-28" style={{ background: '#08080a' }}>
      <div className="mx-auto max-w-5xl px-6 sm:px-8 py-10">

        {/* Verdict card */}
        <VerdictCard scan={scan} />

        {/* AI offline alert banner */}
        {scan.ai_status === 'unavailable' && (
          <div className="mt-4 px-5 py-4 rounded-xl flex items-center gap-3 text-xs"
            style={{ background: 'rgba(202,138,4,0.08)', border: '1px solid rgba(202,138,4,0.2)', color: '#ca8a04' }}>
            <span className="font-semibold">Note:</span> AI behavioral narrative is operating in fallback mode. Threat score, rule triggers, and IOCs are fully verified.
          </div>
        )}

        {/* Tabs & Actions Bar */}
        <div className="mt-10 flex flex-col sm:flex-row sm:items-end justify-between gap-4 border-b border-white/[0.08]">
          <div className="flex items-end gap-1 overflow-x-auto scrollbar-none">
            {TABS.map(t => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className="px-4 py-3 text-xs sm:text-sm font-medium transition-all -mb-px whitespace-nowrap"
                style={{
                  color: tab === t ? '#fafafa' : '#71717a',
                  borderBottom: tab === t ? '2px solid #fafafa' : '2px solid transparent',
                  fontWeight: tab === t ? 600 : 500,
                }}
              >
                {t}
              </button>
            ))}
          </div>

          {/* Download Action Pills */}
          <div className="flex items-center gap-2 pb-2.5">
            <button
              onClick={downloadReport}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium text-zinc-300 hover:text-white transition-colors"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
              <Download className="h-3 w-3" />
              Markdown (.md)
            </button>
            <button
              onClick={downloadPdf}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-mono font-medium text-zinc-300 hover:text-white transition-colors"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)' }}>
              <Download className="h-3 w-3" />
              PDF (.pdf)
            </button>
          </div>
        </div>

        {/* Tab Content Panes */}
        <div className="mt-8">
          {tab === 'Overview' && (
            <div className="flex flex-col gap-8">
              {scan.app_metadata && (
                <div className="rounded-xl overflow-hidden"
                  style={{ background: '#0d0d10', border: '1px solid rgba(255,255,255,0.07)' }}>
                  <div className="px-6 py-4 flex items-center justify-between"
                    style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                    <span className="text-xs font-semibold uppercase tracking-wider text-zinc-400">
                      Extracted Package Metadata
                    </span>
                    <span className="text-xs font-mono text-zinc-500">
                      APK Manifest Analyzer
                    </span>
                  </div>
                  <dl className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-4 text-xs p-6">
                    {Object.entries(scan.app_metadata).map(([k, v]) => (
                      <div key={k} className="flex flex-col gap-1">
                        <dt className="text-zinc-500 font-mono text-[11px] uppercase tracking-wider">
                          {k.replace(/_/g, ' ')}
                        </dt>
                        <dd className="font-mono text-zinc-200 text-xs break-all bg-white/[0.02] px-2.5 py-1.5 rounded border border-white/[0.04]">
                          {String(v) || '—'}
                        </dd>
                      </div>
                    ))}
                  </dl>
                </div>
              )}

              {/* Quick Summary of triggers */}
              <ScoreBreakdown triggers={scan.triggers} />
            </div>
          )}

          {tab === 'Findings & Heuristics' && (
            <div className="flex flex-col gap-8">
              <ScoreBreakdown triggers={scan.triggers} />
              <PermissionTable permissions={scan.permissions} />
            </div>
          )}

          {tab === 'AI Analysis' && (
            <AiFindings scan={scan} />
          )}

          {tab === 'IOCs & Network' && (
            <IocTable iocs={scan.iocs} />
          )}

          {tab === 'Full Report' && (
            <div className="rounded-xl p-8 prose prose-invert prose-base max-w-none shadow-2xl"
              style={{ border: '1px solid rgba(255,255,255,0.08)', background: '#0d0d10' }}>
              <ReactMarkdown>{scan.report_markdown ?? '*No report generated yet.*'}</ReactMarkdown>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}



