import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers.session import router as session_router
from services.ollama import OllamaConnectionError, OllamaError, ollama

logging.basicConfig(level=settings.log_level.upper())

app = FastAPI(title="Resume Tailor", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ollama")
async def health_ollama() -> dict:
    try:
        return await ollama.health()
    except OllamaConnectionError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except OllamaError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
