"""Claude tool-use agent loop.

Turned loose on the mock MemStore with ONLY the provided docs as context and a
single ``call_api`` tool. Used in live mode (an Anthropic key is present). In
replay mode the harness bypasses this module and serves recorded fixtures, so
the demo and smoke test run with no key.

``run_agent_suite`` returns the same fixture shape the replay files use, so a
live run can be saved straight to ``replay/<variant>.json`` to re-record.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
MAX_TURNS = 8

CALL_API_TOOL = {
    "name": "call_api",
    "description": "Make one HTTP request to the MemStore API and get the response.",
    "input_schema": {
        "type": "object",
        "properties": {
            "method": {"type": "string", "enum": ["GET", "POST"]},
            "path": {"type": "string", "description": "e.g. /v1/collections/workspace/documents"},
            "query": {"type": "object", "description": "Query-string params."},
            "headers": {"type": "object", "description": "Request headers, including auth."},
            "body": {"type": "object", "description": "JSON body for POST."},
        },
        "required": ["method", "path"],
    },
}


def _load_docs(variant: str) -> str:
    docs_dir = ROOT / f"docs_{variant}"
    parts = []
    for md in sorted(docs_dir.glob("*.md")):
        parts.append(f"# FILE: {md.name}\n\n{md.read_text()}")
    return "\n\n---\n\n".join(parts)


def _system_prompt(docs: str) -> str:
    return (
        "You are a developer integrating the MemStore API. You may rely ONLY on "
        "the documentation provided below — do not guess at undocumented behaviour. "
        "Use the call_api tool to make requests. When you have completed the task, "
        "state your final answer plainly (for counting tasks, give the number).\n\n"
        "=== DOCUMENTATION ===\n" + docs
    )


def _run_task(client: TestClient, task: dict[str, Any], system: str, model: str) -> dict[str, Any]:
    import anthropic

    llm = anthropic.Anthropic()
    messages: list[dict[str, Any]] = [{"role": "user", "content": task["instruction"]}]
    calls: list[dict[str, Any]] = []
    transcript: list[dict[str, Any]] = []
    answer: Any = None

    for _ in range(MAX_TURNS):
        resp = llm.messages.create(
            model=model, max_tokens=1024, system=system, tools=[CALL_API_TOOL], messages=messages
        )
        messages.append({"role": "assistant", "content": resp.content})
        tool_results = []
        for block in resp.content:
            if block.type == "text" and block.text.strip():
                transcript.append({"role": "assistant", "content": block.text})
                answer = block.text
            elif block.type == "tool_use":
                inp = block.input
                calls.append(inp)
                r = client.request(
                    inp.get("method", "GET"),
                    inp["path"],
                    params=inp.get("query") or None,
                    headers=inp.get("headers") or {},
                    json=inp.get("body"),
                )
                try:
                    payload = r.json()
                except Exception:  # noqa: BLE001
                    payload = r.text
                out = f"{r.status_code} {json.dumps(payload)[:800]}"
                transcript.append({"role": "tool", "content": out})
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": out}
                )
        if tool_results:
            messages.append({"role": "user", "content": tool_results})
        else:
            break

    return {"calls": calls, "answer": answer, "transcript": transcript}


def run_agent_suite(
    variant: str, tasks: list[dict[str, Any]], client: TestClient
) -> dict[str, Any]:  # pragma: no cover - requires a live key
    model = os.getenv("AGENT_MODEL", "claude-sonnet-4-5")
    system = _system_prompt(_load_docs(variant))
    runs = {t["id"]: _run_task(client, t, system, model) for t in tasks}
    return {"variant": variant, "model": model, "runs": runs}
