# Resume Tailor

A local web app that tailors a LaTeX resume to a specific job posting, section by section, using a local LLM running through Ollama. No data leaves your machine.

## How it works

1. **Setup** — paste your `.tex` resume source and the job description (title, company, description).
2. **Wizard** — step through each resume section. The LLM drafts a tailored version, self-critiques it, then rewrites. You can give free-text feedback and regenerate as many times as needed. Accept sections when satisfied.
3. **Review** — once all sections are accepted, run a combined ATS keyword audit and simulated hiring-manager review. Critique items link back to the relevant wizard section.
4. **Export** — copy the fully reassembled LaTeX source, ready to compile.

## Requirements

- Python 3.11+
- Node 18+
- [Ollama](https://ollama.ai) running locally

## Ollama model setup

```bash
# Primary model (~4 GB)
ollama pull qwen2.5:7b-instruct-q4_K_M

# Fallback model (~5 GB) — used automatically if primary is unavailable
ollama pull llama3.1:8b-instruct-q4_K_M
```

Verify Ollama is running before starting the backend:

```bash
ollama list
```

## Setup

### 1. Clone

```bash
git clone https://github.com/jaswanthkolisetty/resume-tailor.git
cd resume-tailor
```

### 2. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Copy and (optionally) edit the environment file:

```bash
cp ../.env.example ../.env
```

Default `.env` values work for a standard local Ollama install. Adjustable settings:

| Variable | Default | Description |
|---|---|---|
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama API base URL |
| `OLLAMA_PRIMARY_MODEL` | `qwen2.5:7b-instruct-q4_K_M` | Primary LLM |
| `OLLAMA_FALLBACK_MODEL` | `llama3.1:8b-instruct-q4_K_M` | Fallback if primary unavailable |
| `OLLAMA_TIMEOUT_SECONDS` | `120` | Per-request timeout |
| `BACKEND_PORT` | `8000` | FastAPI port |

Start the backend:

```bash
uvicorn main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Architecture

```
resume-tailor/
├── backend/
│   ├── main.py                  FastAPI app, CORS, logging
│   ├── config.py                pydantic-settings, reads .env
│   ├── latex_parser.py          .tex string → Resume Pydantic model
│   ├── latex_assembler.py       Resume model → .tex string (round-trip safe)
│   ├── models/
│   │   ├── resume.py            Resume, Section, ExperienceEntry, … models
│   │   └── session.py           Session, SectionState, ReviewResult models
│   ├── services/
│   │   ├── ollama.py            Async Ollama client (primary + fallback, streaming)
│   │   ├── generation.py        LLM orchestration: draft → critique → rewrite
│   │   └── session_manager.py   In-memory session store (dict keyed by UUID)
│   ├── routers/
│   │   └── session.py           6 FastAPI endpoints (start, generate, refine, accept, review, export)
│   └── prompts/
│       ├── section_draft.txt
│       ├── self_critique.txt
│       ├── rewrite_with_feedback.txt
│       ├── ats_review.txt
│       └── human_review.txt
└── frontend/
    └── src/
        ├── App.tsx              3-screen state machine (setup → wizard → review)
        ├── api/client.ts        Typed fetch wrapper for all endpoints
        ├── utils/resumeEntries.ts  Sub-entry parser for Experience / Projects
        └── components/
            ├── SetupScreen.tsx
            ├── SectionSidebar.tsx
            ├── SectionPanel.tsx
            ├── WizardScreen.tsx
            ├── ReviewScreen.tsx
            └── ExportModal.tsx
```

### Request flow

```
Browser (Vite dev server :5173)
    │  Vite proxy strips /session, /health
    ▼
FastAPI (:8000)
    │  POST /session/start          parse LaTeX → create session
    │  POST …/section/{n}/generate  run_section_loop → draft+critique+final
    │  POST …/section/{n}/refine    run_section_loop with user feedback
    │  POST …/section/{n}/accept    apply final bullets → mark accepted
    │  POST …/review                ats_review + human_review in parallel
    │  GET  …/export                assemble(resume) → LaTeX string
    ▼
Ollama (:11434)
    │  /api/generate (non-streaming)
    │  Primary: qwen2.5:7b-instruct-q4_K_M
    └─ Fallback: llama3.1:8b-instruct-q4_K_M
```

## Development

```bash
# Type-check frontend
cd frontend && npx tsc --noEmit

# Lint backend
cd backend && ruff check .

# Run backend tests
cd backend && python -m pytest tests/ -v
```

## Notes

- Sessions are in-memory and lost on backend restart. This is intentional — no persistence layer by design.
- LaTeX is parsed and reassembled with round-trip fidelity. Only the bullet blocks inside `\resumeItemListStart … \resumeItemListEnd` are modified; all other formatting (preamble, contact block, section headers) is preserved verbatim.
- The app expects a Jake's Resume–style `.tex` template. Other templates may parse partially.
