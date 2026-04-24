import { useEffect, useState } from 'react'
import { api } from '../api/client'

interface Props {
  sessionId: string
  sections: string[]
  onGoToSection: (sectionTitle: string) => void
  onBack: () => void
}

interface ParsedAts {
  score: number | null
  matched: string[]
  missing: string[]
  sectionScores: { name: string; score: string; reason: string }[]
  recommendations: string[]
}

interface ParsedHuman {
  firstImpression: string
  strengths: string[]
  concerns: string[]
  narrative: string
  verdict: string
  reason: string
}

// ─── Parsers ──────────────────────────────────────────────────────────────────

function parseAts(text: string): ParsedAts {
  const scoreMatch = text.match(/ATS SCORE:\s*(\d+)/)
  const score = scoreMatch ? parseInt(scoreMatch[1]) : null

  function extractList(header: string): string[] {
    const re = new RegExp(`${header}[:\\s]*\\n((?:\\s*-[^\\n]+\\n?)+)`, 'i')
    const m = text.match(re)
    if (!m) return []
    return m[1].split('\n').map((l) => l.replace(/^\s*-\s*/, '').trim()).filter(Boolean)
  }

  function extractNumberedList(header: string): string[] {
    const re = new RegExp(`${header}[:\\s]*\\n((?:\\s*\\d+\\.[^\\n]+\\n?)+)`, 'i')
    const m = text.match(re)
    if (!m) return []
    return m[1].split('\n').map((l) => l.replace(/^\s*\d+\.\s*/, '').trim()).filter(Boolean)
  }

  const sectionScores: ParsedAts['sectionScores'] = []
  const scoresBlock = text.match(/SECTION SCORES:[:\s]*\n((?:\s*-[^\n]+\n?)+)/i)
  if (scoresBlock) {
    scoresBlock[1].split('\n').forEach((line) => {
      const m = line.match(/^\s*-\s*(.+?):\s*(\d+)\s*(?:—|-)\s*(.+)$/)
      if (m) sectionScores.push({ name: m[1].trim(), score: m[2], reason: m[3].trim() })
    })
  }

  return {
    score,
    matched: extractList('KEYWORDS MATCHED'),
    missing: extractList('KEYWORDS MISSING'),
    sectionScores,
    recommendations: extractNumberedList('TOP 3 RECOMMENDATIONS'),
  }
}

function parseHuman(text: string): ParsedHuman {
  function extract(header: string): string {
    const re = new RegExp(`${header}[^\\n]*\\n([\\s\\S]*?)(?=\\n[A-Z ]+:|$)`, 'i')
    return text.match(re)?.[1]?.trim() ?? ''
  }

  function extractList(header: string): string[] {
    const block = extract(header)
    return block.split('\n').map((l) => l.replace(/^\s*-\s*/, '').trim()).filter(Boolean)
  }

  const verdictMatch = text.match(/VERDICT:\s*(.+)/i)
  const reasonMatch = text.match(/REASON:\s*(.+)/i)

  return {
    firstImpression: extract('FIRST IMPRESSION'),
    strengths: extractList('STRENGTHS'),
    concerns: extractList('CONCERNS'),
    narrative: extract('NARRATIVE COHERENCE'),
    verdict: verdictMatch?.[1]?.trim() ?? '',
    reason: reasonMatch?.[1]?.trim() ?? '',
  }
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

const VERDICT_STYLE: Record<string, string> = {
  'STRONG YES': 'bg-green-100 text-green-700 border-green-200',
  YES: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  MAYBE: 'bg-yellow-100 text-yellow-700 border-yellow-200',
  NO: 'bg-red-100 text-red-700 border-red-200',
}

function matchSection(text: string, sections: string[]): string | null {
  const lower = text.toLowerCase()
  return sections.find((s) => lower.includes(s.toLowerCase().split(' ')[0].toLowerCase())) ?? null
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function CritiqueLine({
  text,
  sections,
  onGoTo,
}: {
  text: string
  sections: string[]
  onGoTo: (s: string) => void
}) {
  const matched = matchSection(text, sections)
  return (
    <li className="flex items-start gap-2 text-sm text-gray-700">
      <span className="mt-0.5 text-gray-400 shrink-0">•</span>
      <span className="flex-1">{text}</span>
      {matched && (
        <button
          onClick={() => onGoTo(matched)}
          className="shrink-0 text-xs text-indigo-600 hover:text-indigo-800 underline"
        >
          Fix →
        </button>
      )}
    </li>
  )
}

function ScoreBar({ score }: { score: number }) {
  const color = score >= 75 ? 'bg-green-500' : score >= 50 ? 'bg-yellow-500' : 'bg-red-500'
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${score}%` }} />
      </div>
      <span className="text-sm font-semibold text-gray-700 w-8 text-right">{score}</span>
    </div>
  )
}

// ─── Main component ───────────────────────────────────────────────────────────

export function ReviewScreen({ sessionId, sections, onGoToSection, onBack }: Props) {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [atsText, setAtsText] = useState('')
  const [humanText, setHumanText] = useState('')

  useEffect(() => {
    api
      .reviewSession(sessionId)
      .then((res) => {
        setAtsText(res.ats_review)
        setHumanText(res.human_review)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Review failed'))
      .finally(() => setLoading(false))
  }, [sessionId])

  const ats = parseAts(atsText)
  const human = parseHuman(humanText)
  const verdictStyle = VERDICT_STYLE[human.verdict] ?? 'bg-gray-100 text-gray-700 border-gray-200'

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Top bar */}
      <header className="h-12 bg-white border-b border-gray-200 flex items-center justify-between px-5 shrink-0">
        <button onClick={onBack} className="text-sm text-gray-500 hover:text-gray-800">
          ← Back to wizard
        </button>
        <span className="text-sm font-semibold text-gray-800">Review</span>
        <div className="w-24" />
      </header>

      {loading && (
        <div className="flex-1 flex items-center justify-center gap-2 text-sm text-gray-400">
          <span className="animate-spin">◌</span>
          Running ATS + human review…
        </div>
      )}

      {error && (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
            {error}
          </p>
        </div>
      )}

      {!loading && !error && (
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-5xl mx-auto grid grid-cols-2 gap-6">
            {/* ATS Panel */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-5">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-gray-900">ATS Score</h2>
                {ats.score !== null && <ScoreBar score={ats.score} />}
              </div>

              {ats.missing.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Missing Keywords
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {ats.missing.map((kw) => (
                      <span
                        key={kw}
                        className="text-xs bg-red-50 text-red-700 border border-red-200 rounded-full px-2.5 py-0.5"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {ats.matched.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Matched Keywords
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {ats.matched.map((kw) => (
                      <span
                        key={kw}
                        className="text-xs bg-green-50 text-green-700 border border-green-200 rounded-full px-2.5 py-0.5"
                      >
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {ats.sectionScores.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Section Scores
                  </h3>
                  <ul className="space-y-2">
                    {ats.sectionScores.map((s) => (
                      <li key={s.name} className="text-sm">
                        <div className="flex items-center justify-between mb-0.5">
                          <span className="text-gray-700">{s.name}</span>
                          <span className="text-gray-500 text-xs">{s.score}/100</span>
                        </div>
                        <p className="text-xs text-gray-400">{s.reason}</p>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {ats.recommendations.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Top Recommendations
                  </h3>
                  <ol className="space-y-1.5 list-decimal list-inside">
                    {ats.recommendations.map((r, i) => (
                      <CritiqueLine key={i} text={r} sections={sections} onGoTo={onGoToSection} />
                    ))}
                  </ol>
                </div>
              )}
            </div>

            {/* Human Review Panel */}
            <div className="bg-white rounded-xl border border-gray-200 p-5 flex flex-col gap-5">
              <div className="flex items-center justify-between">
                <h2 className="font-semibold text-gray-900">Hiring Manager View</h2>
                {human.verdict && (
                  <span
                    className={`text-xs font-semibold border rounded-full px-2.5 py-0.5 ${verdictStyle}`}
                  >
                    {human.verdict}
                  </span>
                )}
              </div>

              {human.firstImpression && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    First Impression
                  </h3>
                  <p className="text-sm text-gray-700 leading-relaxed">{human.firstImpression}</p>
                </div>
              )}

              {human.strengths.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Strengths
                  </h3>
                  <ul className="space-y-1">
                    {human.strengths.map((s, i) => (
                      <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                        <span className="mt-0.5 text-green-500 shrink-0">✓</span>
                        {s}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {human.concerns.length > 0 && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
                    Concerns
                  </h3>
                  <ul className="space-y-2">
                    {human.concerns.map((c, i) => (
                      <CritiqueLine key={i} text={c} sections={sections} onGoTo={onGoToSection} />
                    ))}
                  </ul>
                </div>
              )}

              {human.narrative && (
                <div>
                  <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
                    Narrative
                  </h3>
                  <p className="text-sm text-gray-700 leading-relaxed">{human.narrative}</p>
                </div>
              )}

              {human.reason && (
                <p className="text-sm text-gray-500 italic border-t border-gray-100 pt-3">
                  {human.reason}
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
