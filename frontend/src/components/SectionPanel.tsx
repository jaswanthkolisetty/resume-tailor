import { useState } from 'react'

type Tab = 'final' | 'draft' | 'critique'

interface SectionState {
  status: 'pending' | 'generating' | 'draft_ready' | 'accepted'
  draft: string
  critique: string
  final: string
  user_feedback: string
}

interface Props {
  sectionTitle: string
  state: SectionState
  onGenerate: () => Promise<void>
  onRefine: (feedback: string) => Promise<void>
  onAccept: () => Promise<void>
}

export function SectionPanel({ sectionTitle, state, onGenerate, onRefine, onAccept }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>('final')
  const [feedback, setFeedback] = useState(state.user_feedback ?? '')
  const [busy, setBusy] = useState(false)

  const hasContent = state.status === 'draft_ready' || state.status === 'accepted'
  const isAccepted = state.status === 'accepted'
  const isGenerating = state.status === 'generating' || busy

  async function handleGenerate() {
    setBusy(true)
    try {
      await onGenerate()
      setActiveTab('final')
    } finally {
      setBusy(false)
    }
  }

  async function handleRefine() {
    setBusy(true)
    try {
      await onRefine(feedback)
      setActiveTab('final')
    } finally {
      setBusy(false)
    }
  }

  async function handleAccept() {
    setBusy(true)
    try {
      await onAccept()
    } finally {
      setBusy(false)
    }
  }

  const tabContent: Record<Tab, string> = {
    final: state.final,
    draft: state.draft,
    critique: state.critique,
  }

  return (
    <div className="flex flex-col h-full p-6 gap-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">{sectionTitle}</h2>
        {isAccepted && (
          <span className="text-xs font-medium text-green-600 bg-green-50 border border-green-200 rounded-full px-2.5 py-0.5">
            Accepted
          </span>
        )}
      </div>

      {/* Pending state */}
      {state.status === 'pending' && !busy && (
        <div className="flex-1 flex flex-col items-center justify-center gap-3 text-center">
          <p className="text-sm text-gray-500">
            Ready to tailor this section to your target role.
          </p>
          <button
            onClick={handleGenerate}
            className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
          >
            Generate
          </button>
        </div>
      )}

      {/* Generating spinner */}
      {isGenerating && (
        <div className="flex-1 flex items-center justify-center gap-2 text-sm text-gray-400">
          <span className="animate-spin">◌</span>
          Generating…
        </div>
      )}

      {/* Content tabs */}
      {hasContent && !isGenerating && (
        <>
          <div className="flex gap-1 border-b border-gray-200">
            {(['final', 'draft', 'critique'] as Tab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-3 py-1.5 text-sm capitalize transition-colors border-b-2 -mb-px ${
                  activeTab === tab
                    ? 'border-indigo-600 text-indigo-700 font-medium'
                    : 'border-transparent text-gray-500 hover:text-gray-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>

          <div className="flex-1 overflow-y-auto rounded-lg border border-gray-200 bg-gray-50 p-4">
            <pre className="text-sm text-gray-800 whitespace-pre-wrap font-sans leading-relaxed">
              {tabContent[activeTab] || (
                <span className="text-gray-400 italic">No content yet.</span>
              )}
            </pre>
          </div>

          {/* Feedback + actions */}
          {!isAccepted && (
            <div className="flex flex-col gap-3">
              <textarea
                rows={3}
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                placeholder="Optional feedback — e.g. 'emphasise the RAG pipeline more' or 'remove the Spark bullet'"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              />
              <div className="flex gap-2 justify-end">
                <button
                  onClick={handleRefine}
                  disabled={busy}
                  className="bg-white hover:bg-gray-50 disabled:opacity-50 border border-gray-300 text-gray-700 text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                >
                  Regenerate
                </button>
                <button
                  onClick={handleAccept}
                  disabled={busy}
                  className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
                >
                  Accept
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
