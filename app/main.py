"""AgentReady harness — FastAPI app.

Serves (a) the mock MemStore API (``/v1``), (b) the harness endpoints (``/api``),
and (c) the static dashboard (``/``). ``make run`` boots everything on
localhost:8000.
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from app.harness import load_tasks, resolve_mode, run_suite
from app.memstore import MemStore, router as memstore_router

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = MemStore()
    store.seed()
    app.state.memstore = store
    yield


app = FastAPI(title="AgentReady Harness", version="1.0.0", lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


# --------------------------------------------------------------------------- #
# Harness API
# --------------------------------------------------------------------------- #
@app.get("/api/config")
def api_config() -> dict[str, object]:
    return {
        "mode": resolve_mode(),
        "has_key": bool(os.getenv("ANTHROPIC_API_KEY")),
        "replay_only": os.getenv("REPLAY_ONLY") == "1",
        "model": os.getenv("AGENT_MODEL", "claude-sonnet-4-5"),
    }


@app.get("/api/tasks")
def api_tasks() -> dict[str, object]:
    return {"tasks": load_tasks()}


@app.post("/api/run/{variant}")
def api_run(variant: str) -> JSONResponse:
    if variant not in ("gapped", "fixed"):
        return JSONResponse({"error": "variant must be 'gapped' or 'fixed'"}, status_code=400)
    return JSONResponse(run_suite(variant))


# --------------------------------------------------------------------------- #
# Mock MemStore API
# --------------------------------------------------------------------------- #
app.include_router(memstore_router)


# --------------------------------------------------------------------------- #
# Dashboard (static)
# --------------------------------------------------------------------------- #
@app.get("/")
def dashboard() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
