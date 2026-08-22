import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { CloudUpload, FileWarning, Loader2 } from 'lucide-react'
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
      setError('Only .apk files are accepted.')
      return
    }
    if (file.size > 100 * 1024 * 1024) {
      setError('File exceeds 100 MB limit.')
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
      else if (status === 415) setError('Invalid file — must be an APK.')
      else if (status === 429) setError('Server busy — too many scans running. Try in a moment.')
      else setError('Upload failed. Is the backend running?')
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
    <div
      id="dropzone"
      onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={onDrop}
      className={`relative flex flex-col items-center justify-center rounded-2xl border-2 border-dashed p-12 text-center transition-all duration-300 cursor-pointer
        ${dragging
          ? 'border-red-400 bg-red-500/10 scale-[1.01]'
          : 'border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]'
        }`}
      onClick={() => !loading && document.getElementById('apk-file-input').click()}
    >
      <input
        id="apk-file-input"
        type="file"
        accept=".apk"
        className="hidden"
        onChange={onInputChange}
      />

      {loading ? (
        <>
          <Loader2 className="h-12 w-12 animate-spin text-red-400 mb-4" />
          <p className="text-lg font-semibold text-white">Uploading & queuing scan…</p>
        </>
      ) : (
        <>
          <div className={`mb-6 flex h-20 w-20 items-center justify-center rounded-2xl transition-all
            ${dragging ? 'bg-red-500/20' : 'bg-white/5'}`}>
            <CloudUpload className={`h-10 w-10 transition-colors ${dragging ? 'text-red-400' : 'text-slate-400'}`} />
          </div>
          <p className="mb-2 text-xl font-bold text-white">Drop APK here to scan</p>
          <p className="text-sm text-slate-400">or click to browse · max 100 MB</p>

          {error && (
            <div className="mt-6 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-2 text-sm text-red-400">
              <FileWarning className="h-4 w-4 flex-shrink-0" />
              {error}
            </div>
          )}
        </>
      )}
    </div>
  )
}
