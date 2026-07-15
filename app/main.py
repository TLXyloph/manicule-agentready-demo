"""AgentReady harness — FastAPI app.

Serves (a) the mock MemStore API, (b) the harness endpoints, and (c) the static
dashboard. This iteration wires up (a); the harness endpoints and dashboard are
added in later iterations.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.memstore import MemStore, router as memstore_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    store = MemStore()
    store.seed()
    app.state.memstore = store
    yield


app = FastAPI(title="AgentReady Harness", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(memstore_router)
