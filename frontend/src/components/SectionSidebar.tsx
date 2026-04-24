interface SectionMeta {
  title: string
  status: 'pending' | 'generating' | 'draft_ready' | 'accepted'
}

interface Props {
  sections: SectionMeta[]
  activeSection: string
  onSelect: (title: string) => void
}

const STATUS_ICON: Record<SectionMeta['status'], string> = {
  pending: '○',
  generating: '◌',
  draft_ready: '●',
  accepted: '✓',
}

const STATUS_COLOR: Record<SectionMeta['status'], string> = {
  pending: 'text-gray-400',
  generating: 'text-yellow-500 animate-pulse',
  draft_ready: 'text-indigo-500',
  accepted: 'text-green-500',
}

export function SectionSidebar({ sections, activeSection, onSelect }: Props) {
  return (
    <nav className="w-56 shrink-0 border-r border-gray-200 bg-white h-full overflow-y-auto">
      <div className="px-4 py-4 border-b border-gray-100">
        <p className="text-xs font-semibold text-gray-400 uppercase tracking-wider">Sections</p>
      </div>
      <ul className="py-2">
        {sections.map((s) => {
          const isActive = s.title === activeSection
          return (
            <li key={s.title}>
              <button
                onClick={() => onSelect(s.title)}
                className={`w-full flex items-center gap-2.5 px-4 py-2.5 text-left text-sm transition-colors ${
                  isActive
                    ? 'bg-indigo-50 text-indigo-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <span className={`text-xs shrink-0 ${STATUS_COLOR[s.status]}`}>
                  {STATUS_ICON[s.status]}
                </span>
                <span className="truncate">{s.title}</span>
              </button>
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
