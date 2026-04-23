const BASE = ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(detail?.detail ?? res.statusText)
  }
  return res.json() as Promise<T>
}

export interface StartResponse {
  session_id: string
  sections: string[]
  status: string
}

export interface SectionResponse {
  draft: string
  critique: string
  final: string
  status: string
}

export interface ReviewResponse {
  ats_review: string
  human_review: string
}

export interface ExportResponse {
  latex: string
}

export const api = {
  startSession: (payload: {
    resume_latex: string
    job_title: string
    company_name: string
    job_description: string
  }) =>
    request<StartResponse>('/session/start', {
      method: 'POST',
      body: JSON.stringify(payload),
    }),

  generateSection: (sessionId: string, sectionName: string) =>
    request<SectionResponse>(
      `/session/${sessionId}/section/${encodeURIComponent(sectionName)}/generate`,
      { method: 'POST' },
    ),

  refineSection: (sessionId: string, sectionName: string, userFeedback: string) =>
    request<SectionResponse>(
      `/session/${sessionId}/section/${encodeURIComponent(sectionName)}/refine`,
      { method: 'POST', body: JSON.stringify({ user_feedback: userFeedback }) },
    ),

  acceptSection: (sessionId: string, sectionName: string) =>
    request<{ section: string; status: string }>(
      `/session/${sessionId}/section/${encodeURIComponent(sectionName)}/accept`,
      { method: 'POST' },
    ),

  reviewSession: (sessionId: string) =>
    request<ReviewResponse>(`/session/${sessionId}/review`, { method: 'POST' }),

  exportSession: (sessionId: string) =>
    request<ExportResponse>(`/session/${sessionId}/export`),
}
