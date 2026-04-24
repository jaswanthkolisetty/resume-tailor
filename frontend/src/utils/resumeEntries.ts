export interface EntryMeta {
  title: string
  bulletCount: number
}

function extractBraced(tex: string, pos: number): [string, number] {
  let depth = 0
  let i = pos
  while (i < tex.length) {
    if (tex[i] === '\\') { i += 2; continue }
    if (tex[i] === '{') depth++
    else if (tex[i] === '}') { depth--; if (depth === 0) return [tex.slice(pos + 1, i), i + 1] }
    i++
  }
  return ['', pos]
}

function sectionBody(tex: string, title: string): string {
  const escaped = title.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const re = new RegExp(`\\\\section\\{${escaped}\\}([\\s\\S]*?)(?=\\\\section\\{|\\\\end\\{document\\})`)
  return re.exec(tex)?.[1] ?? ''
}

function countBulletsUntilNext(body: string, from: number, nextAt: number): number {
  const region = body.slice(from, nextAt === -1 ? undefined : nextAt)
  return (region.match(/\\resumeItem\s*\{/g) ?? []).length
}

export function extractEntryMetas(tex: string, sectionTitle: string): EntryMeta[] {
  const body = sectionBody(tex, sectionTitle)
  if (!body) return []

  const isExperience = /experience|work/i.test(sectionTitle)
  const isProject = /project/i.test(sectionTitle)

  const entries: EntryMeta[] = []

  if (isExperience) {
    const re = /\\resumeSubheading\s*\{/g
    const positions: number[] = []
    let m: RegExpExecArray | null
    while ((m = re.exec(body)) !== null) positions.push(m.index)

    positions.forEach((pos, i) => {
      const [company] = extractBraced(body, body.indexOf('{', pos))
      const nextPos = positions[i + 1] ?? -1
      const bulletCount = countBulletsUntilNext(body, pos, nextPos)
      entries.push({ title: company.trim(), bulletCount: Math.max(bulletCount, 1) })
    })
  } else if (isProject) {
    const re = /\\resumeProjectHeading\s*\{/g
    const positions: number[] = []
    let m: RegExpExecArray | null
    while ((m = re.exec(body)) !== null) positions.push(m.index)

    positions.forEach((pos, i) => {
      const [heading] = extractBraced(body, body.indexOf('{', pos))
      // Strip \textbf{name} -- technologies
      const name = heading.replace(/\\textbf\{([^}]+)\}/, '$1').split(/\s*--\s*/)[0].trim()
      const nextPos = positions[i + 1] ?? -1
      const bulletCount = countBulletsUntilNext(body, pos, nextPos)
      entries.push({ title: name, bulletCount: Math.max(bulletCount, 1) })
    })
  }

  return entries
}

export function splitFinalBullets(finalText: string, metas: EntryMeta[]): string[] {
  if (!metas.length) return [finalText]

  const lines = finalText
    .split('\n')
    .map((l) => l.replace(/^[-•*]\s*/, '').trim())
    .filter((l) => l.length > 2)

  const total = metas.reduce((s, m) => s + m.bulletCount, 0)
  const chunks: string[] = []
  let start = 0

  metas.forEach((meta, i) => {
    const take =
      i === metas.length - 1
        ? lines.length - start
        : Math.max(1, Math.round((lines.length * meta.bulletCount) / total))
    chunks.push(lines.slice(start, start + take).map((l) => `- ${l}`).join('\n'))
    start += take
  })

  return chunks
}
