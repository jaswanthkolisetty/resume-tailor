import { useEffect, useMemo, useState } from 'react'
import { api } from '../api/client'
import { extractEntryMetas, splitFinalBullets } from '../utils/resumeEntries'
import { ExportModal } from './ExportModal'
import { type EntryNav, SectionPanel } from './SectionPanel'
import { SectionSidebar } from './SectionSidebar'

interface SectionState {
  status: 'pending' | 'generating' | 'draft_ready' | 'accepted'
  draft: string
  critique: string
  final: string
  user_feedback: string
}

interface Props {
  sessionId: string
  sections: string[]
  resumeLatex: string
  initialSection?: string
  onReviewReady: (sessionId: string) => void
}

function isMultiEntry(title: string) {
  return /experience|work|project/i.test(title)
}

const INITIAL_STATE: SectionState = {
  status: 'pending',
  draft: '',
  critique: '',
  final: '',
  user_feedback: '',
}

export function WizardScreen({ sessionId, sections, resumeLatex, initialSection, onReviewReady }: Props) {
  const [activeSection, setActiveSection] = useState(initialSection ?? sections[0] ?? '')
  const [sectionStates, setSectionStates] = useState<Record<string, SectionState>>(() =>
    Object.fromEntries(sections.map((s) => [s, { ...INITIAL_STATE }])),
  )
  const [entryIndices, setEntryIndices] = useState<Record<string, number>>({})
  const [showExport, setShowExport] = useState(false)

  // Entry metadata parsed once from the original LaTeX
  const entryMetas = useMemo(
    () =>
      Object.fromEntries(
        sections.filter(isMultiEntry).map((s) => [s, extractEntryMetas(resumeLatex, s)]),
      ),
    [resumeLatex, sections],
  )

  // Initialise entry indices for multi-entry sections
  useEffect(() => {
    const initial: Record<string, number> = {}
    sections.filter(isMultiEntry).forEach((s) => { initial[s] = 0 })
    setEntryIndices(initial)
  }, [sections])

  function updateSection(title: string, patch: Partial<SectionState>) {
    setSectionStates((prev) => ({
      ...prev,
      [title]: { ...prev[title], ...patch },
    }))
  }

  async function handleGenerate(title: string) {
    updateSection(title, { status: 'generating' })
    try {
      const res = await api.generateSection(sessionId, title)
      updateSection(title, {
        status: 'draft_ready',
        draft: res.draft,
        critique: res.critique,
        final: res.final,
      })
    } catch {
      updateSection(title, { status: 'pending' })
    }
  }

  async function handleRefine(title: string, feedback: string) {
    updateSection(title, { status: 'generating', user_feedback: feedback })
    try {
      const res = await api.refineSection(sessionId, title, feedback)
      updateSection(title, {
        status: 'draft_ready',
        draft: res.draft,
        critique: res.critique,
        final: res.final,
      })
    } catch {
      updateSection(title, { status: 'draft_ready' })
    }
  }

  async function handleAccept(title: string) {
    await api.acceptSection(sessionId, title)
    updateSection(title, { status: 'accepted' })
  }

  const sidebarSections = sections.map((title) => ({
    title,
    status: sectionStates[title]?.status ?? 'pending',
  }))

  const activeState = sectionStates[activeSection] ?? { ...INITIAL_STATE }
  const metas = entryMetas[activeSection]
  const entryIdx = entryIndices[activeSection] ?? 0

  let entryNav: EntryNav | undefined
  if (metas && metas.length > 1 && activeState.final) {
    const chunks = splitFinalBullets(activeState.final, metas)
    entryNav = {
      current: entryIdx,
      total: metas.length,
      title: metas[entryIdx]?.title ?? '',
      entryFinal: chunks[entryIdx] ?? '',
      onPrev: () => setEntryIndices((p) => ({ ...p, [activeSection]: Math.max(0, entryIdx - 1) })),
      onNext: () =>
        setEntryIndices((p) => ({
          ...p,
          [activeSection]: Math.min(metas.length - 1, entryIdx + 1),
        })),
    }
  }

  const allAccepted = sections.every((s) => sectionStates[s]?.status === 'accepted')

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Top bar */}
      <header className="h-12 bg-white border-b border-gray-200 flex items-center justify-between px-5 shrink-0">
        <span className="text-sm font-semibold text-gray-800">Resume Tailor</span>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowExport(true)}
            className="text-sm font-medium border border-gray-300 hover:bg-gray-50 text-gray-700 px-4 py-1.5 rounded-lg transition-colors"
          >
            Export
          </button>
          <button
            onClick={() => onReviewReady(sessionId)}
            disabled={!allAccepted}
            className="text-sm font-medium bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-200 disabled:text-gray-400 text-white px-4 py-1.5 rounded-lg transition-colors"
          >
            Run Review →
          </button>
        </div>
      </header>

      {/* Main layout */}
      <div className="flex flex-1 overflow-hidden">
        <SectionSidebar
          sections={sidebarSections}
          activeSection={activeSection}
          onSelect={(title) => {
            setActiveSection(title)
            if (entryIndices[title] === undefined && isMultiEntry(title)) {
              setEntryIndices((p) => ({ ...p, [title]: 0 }))
            }
          }}
        />

        <main className="flex-1 overflow-y-auto">
          <SectionPanel
            key={activeSection}
            sectionTitle={activeSection}
            state={activeState}
            entryNav={entryNav}
            onGenerate={() => handleGenerate(activeSection)}
            onRefine={(fb) => handleRefine(activeSection, fb)}
            onAccept={() => handleAccept(activeSection)}
          />
        </main>
      </div>

      {showExport && <ExportModal sessionId={sessionId} onClose={() => setShowExport(false)} />}
    </div>
  )
}
