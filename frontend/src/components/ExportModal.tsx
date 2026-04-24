import { useEffect, useState } from 'react'
import { api } from '../api/client'

interface Props {
  sessionId: string
  onClose: () => void
}

export function ExportModal({ sessionId, onClose }: Props) {
  const [latex, setLatex] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    api
      .exportSession(sessionId)
      .then((res) => setLatex(res.latex))
      .catch((err) => setError(err instanceof Error ? err.message : 'Export failed'))
      .finally(() => setLoading(false))
  }, [sessionId])

  async function handleCopy() {
    await navigator.clipboard.writeText(latex)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/40"
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="w-full max-w-3xl bg-white rounded-2xl shadow-xl flex flex-col max-h-[80vh]">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-200 shrink-0">
          <h2 className="font-semibold text-gray-900">Export LaTeX</h2>
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopy}
              disabled={loading || !!error}
              className="text-sm font-medium bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-200 disabled:text-gray-400 text-white px-4 py-1.5 rounded-lg transition-colors"
            >
              {copied ? 'Copied!' : 'Copy'}
            </button>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 text-xl leading-none px-1"
            >
              ×
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-5">
          {loading && (
            <div className="flex items-center justify-center gap-2 py-12 text-sm text-gray-400">
              <span className="animate-spin">◌</span>
              Assembling LaTeX…
            </div>
          )}
          {error && (
            <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </p>
          )}
          {!loading && !error && (
            <pre className="text-xs font-mono text-gray-800 whitespace-pre-wrap break-all leading-relaxed bg-gray-50 rounded-lg p-4 border border-gray-200">
              {latex}
            </pre>
          )}
        </div>
      </div>
    </div>
  )
}
