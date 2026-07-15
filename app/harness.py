"""AgentReady harness — orchestrates a task-suite run against the mock API.

For each task the harness obtains a sequence of API calls plus a self-report
(either from the deterministic replay fixtures, or, with a live key, from the
Claude tool-use agent), executes those calls against a *fresh, seeded* MemStore
so side effects are real, then runs the deterministic checker and attributes any
failure to a named doc gap.

The same code path serves live and replay; only the source of the calls differs.
This is what lets the smoke test and the dashboard reproduce the before/after
jump with NO Anthropic key.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.checkers import run_checker
from app.memstore import MemStore, router as memstore_router
from app.scoring import attribute_failure, score_run

ROOT = Path(__file__).resolve().parent.parent
TASKS_PATH = ROOT / "tasks" / "tasks.json"
REPLAY_DIR = ROOT / "replay"


def load_tasks() -> list[dict[str, Any]]:
    return json.loads(TASKS_PATH.read_text())["tasks"]


def resolve_mode(requested: str | None = None) -> str:
    """Decide replay vs live. Replay wins with no key or REPLAY_ONLY=1."""
    if requested in ("replay", "live"):
        forced = requested
    else:
        forced = None
    if os.getenv("REPLAY_ONLY") == "1" or not os.getenv("ANTHROPIC_API_KEY"):
        return "replay"
    return forced or "live"


def _fresh_client() -> tuple[TestClient, MemStore]:
    store = MemStore()
    store.seed()
    app = FastAPI()
    app.state.memstore = store
    app.include_router(memstore_router)
    return TestClient(app), store


def _execute_calls(client: TestClient, calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    log: list[dict[str, Any]] = []
    for c in calls:
        resp = client.request(
            c.get("method", "GET"),
            c["path"],
            params=c.get("query") or None,
            headers=c.get("headers") or {},
            json=c.get("body"),
        )
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001
            body = resp.text
        log.append(
            {
                "method": c.get("method", "GET"),
                "path": c["path"],
                "query": c.get("query"),
                "auth": _auth_summary(c.get("headers") or {}),
                "status": resp.status_code,
                "response": body,
            }
        )
    return log


def _auth_summary(headers: dict[str, Any]) -> str:
    if "X-MemStore-Key" in headers:
        return "X-MemStore-Key"
    if "Authorization" in headers:
        return headers["Authorization"].split(" ")[0]
    return "none"


def _load_replay(variant: str) -> dict[str, Any]:
    path = REPLAY_DIR / f"{variant}.json"
    if not path.exists():
        raise FileNotFoundError(f"missing replay fixture: {path}")
    return json.loads(path.read_text())


def run_suite(variant: str, mode: str | None = None) -> dict[str, Any]:
    """Run the full task suite against the given docs variant ('gapped'|'fixed')."""
    if variant not in ("gapped", "fixed"):
        raise ValueError(f"unknown variant {variant!r}")
    resolved = resolve_mode(mode)
    tasks = load_tasks()
    client, store = _fresh_client()

    if resolved == "replay":
        fixture = _load_replay(variant)
    else:  # pragma: no cover - only with a live key
        from app.agent import run_agent_suite

        fixture = run_agent_suite(variant, tasks, client)

    runs = fixture.get("runs", {})
    task_results: list[dict[str, Any]] = []
    for task in tasks:
        run = runs.get(task["id"], {"calls": [], "answer": None, "transcript": []})
        call_log = _execute_calls(client, run.get("calls", []))
        answer = run.get("answer")
        passed, detail = run_checker(task["id"], store, answer)
        gap = None if passed else attribute_failure(task)
        task_results.append(
            {
                "id": task["id"],
                "title": task["title"],
                "instruction": task["instruction"],
                "requires": task.get("requires"),
                "expected": task.get("expected"),
                "answer": answer,
                "passed": passed,
                "detail": detail,
                "gap": gap,
                "calls": call_log,
                "transcript": run.get("transcript", []),
            }
        )

    summary = score_run(task_results)
    return {
        "variant": variant,
        "mode": resolved,
        "tasks": task_results,
        **summary,
    }
