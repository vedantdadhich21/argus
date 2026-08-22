import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, UploadCloud, Shield } from 'lucide-react'
import { api, USE_MOCKS } from '../../api/client'
import mockData from '../../mocks/scanResponse.json'

export default function Dropzone() {
  const [dragging, setDragging] = useState(false)
  const [error, setError]       = useState(null)
  const [loading, setLoading]   = useState(false)
  const navigate = useNavigate()

  const handleFile = useCallback(async (file) => {
    setError(null)
    if (!file) return
    if (!file.name.endsWith('.apk')) {
      setError('Only .apk files are supported for behavioral threat analysis.')
      return
    }
    if (file.size > 100 * 1024 * 1024) {
      setError('File exceeds 100 MB maximum size limit.')
      return
    }

    setLoading(true)
    try {
      if (USE_MOCKS) {
        await new Promise(r => setTimeout(r, 800))
        navigate(`/scan/${mockData.scan_id}`)
        return
      }
      const form = new FormData()
      form.append('file', file)
      const { data } = await api.post('/api/scan', form)
      navigate(`/scan/${data.scan_id}`)
    } catch (err) {
      const status = err.response?.status
      if (status === 413) setError('File too large (max 100 MB).')
      else if (status === 415) setError('Invalid package format — must be an Android APK.')
      else if (status === 429) setError('Analysis pipeline at capacity — please retry in a moment.')
      else setError('Upload failed. Check if the backend API service is running.')
    } finally {
      setLoading(false)
    }
  }, [navigate])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }, [handleFile])

  const onInputChange = (e) => handleFile(e.target.files[0])

  return (
    <div className="w-full">
      <div
        id="dropzone"
        onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => !loading && document.getElementById('apk-file-input').click()}
        className="relative flex flex-col items-center justify-center cursor-pointer py-16 sm:py-20 px-8 rounded-xl transition-all duration-200 group overflow-hidden"
        style={{
          border: dragging
            ? '1.5px dashed rgba(56,189,248,0.7)'
            : '1px dashed rgba(255,255,255,0.12)',
          background: dragging
            ? 'radial-gradient(circle at 50% 50%, rgba(56,189,248,0.06), #101014 80%)'
            : 'radial-gradient(circle at 50% 50%, rgba(255,255,255,0.03), #0d0d10 85%)',
          boxShadow: dragging
            ? '0 0 30px -5px rgba(56,189,248,0.15)'
            : '0 4px 20px -2px rgba(0,0,0,0.5)',
        }}
      >
        {/* Subtle grid texture inside dropzone */}
        <div className="absolute inset-0 bg-dot-pattern opacity-40 pointer-events-none" />

        <input
          id="apk-file-input"
          type="file"
          accept=".apk"
          className="hidden"
          onChange={onInputChange}
        />

        {loading ? (
          <div className="relative z-10 flex flex-col items-center gap-3.5">
            <div className="h-12 w-12 rounded-full flex items-center justify-center"
              style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)' }}>
              <Loader2 className="h-6 w-6 animate-spin text-white" />
            </div>
            <p className="text-sm font-medium text-white">Uploading & dispatching to pipeline…</p>
            <p className="text-xs font-mono text-zinc-500">Decompiling bytecode & extracting manifest</p>
          </div>
        ) : (
          <div className="relative z-10 flex flex-col items-center gap-3 text-center max-w-md">
            <div className="h-12 w-12 rounded-xl flex items-center justify-center mb-1 transition-transform duration-200 group-hover:scale-105"
              style={{
                background: dragging ? 'rgba(56,189,248,0.12)' : 'rgba(255,255,255,0.05)',
                border: dragging ? '1px solid rgba(56,189,248,0.3)' : '1px solid rgba(255,255,255,0.08)'
              }}>
              <UploadCloud className={`h-6 w-6 transition-colors ${dragging ? 'text-sky-400' : 'text-zinc-300 group-hover:text-white'}`} />
            </div>
            
            <p className="text-base sm:text-lg font-medium text-white tracking-tight">
              Drop Android APK here to analyze
            </p>
            
            <p className="text-xs sm:text-sm text-zinc-400">
              or <span className="text-zinc-200 underline underline-offset-4 group-hover:text-white">browse local files</span> · .apk packages up to 100 MB
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-3.5 p-3 rounded-lg flex items-center justify-center gap-2 text-xs font-medium"
          style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)', color: '#f87171' }}>
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}



