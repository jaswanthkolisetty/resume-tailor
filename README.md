# Resume Tailor

A local web app that takes a base LaTeX resume and a job description, then walks through tailoring the resume section-by-section using a local LLM (Ollama).

## Features

- Section-by-section resume tailoring wizard
- LLM self-critique and rewrite loop
- Per-section feedback memory
- ATS + human-reviewer critique pass
- Final reassembled LaTeX output for copy-paste

## Requirements

- Python 3.11+
- Node 18+
- [Ollama](https://ollama.ai) running locally

## Ollama Models

```bash
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull llama3.1:8b-instruct-q4_K_M   # fallback
```

## Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp ../.env.example ../.env
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Architecture

```
backend/
  models/        Pydantic data models
  services/      Ollama client, generation orchestration, session manager
  routers/       FastAPI route handlers
  prompts/       LLM prompt templates
  latex_parser.py    .tex string → Resume model
  latex_assembler.py Resume model → .tex string
  main.py        FastAPI app entry point
frontend/
  src/
    components/  React components
    api/         API client
```
