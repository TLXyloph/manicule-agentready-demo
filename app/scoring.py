"""Scoring + gap-attribution engine.

Given per-task pass/fail, attribute each failure to the responsible named doc
gap via a rule table (capability -> gap). An optional LLM-judge fallback is
wired in for failures the rule table cannot explain, but it is only consulted
when a live Anthropic key is present; the deterministic path never needs it.
"""

from __future__ import annotations

import os
from typing import Any, Optional

# --------------------------------------------------------------------------- #
# The named doc gaps. Each corresponds to a section that docs_gapped/ gets
# wrong or omits and docs_fixed/ completes.
# --------------------------------------------------------------------------- #
GAPS: dict[str, dict[str, str]] = {
    "undocumented-metadata-filter": {
        "id": "undocumented-metadata-filter",
        "capability": "filter",
        "title": "SQL-style metadata filter is undocumented",
        "doc": "docs_gapped/api-reference.md",
        "symptom": "The `filter` query parameter is missing from the gapped docs, "
        "so the agent cannot query metadata server-side and only sees the first "
        "page — it under-counts.",
        "fix": "Documented the `filter` query param with SQL-style syntax and operators.",
    },
    "missing-pagination-cursor": {
        "id": "missing-pagination-cursor",
        "capability": "cursor",
        "title": "Pagination cursor field is missing",
        "doc": "docs_gapped/api-reference.md",
        "symptom": "The `next_cursor` response field and `cursor` query param are "
        "absent from the gapped docs, so the agent never pages past the first "
        "results and misses most documents.",
        "fix": "Documented the `next_cursor` response field and the `cursor` query param.",
    },
    "auth-header-contradiction": {
        "id": "auth-header-contradiction",
        "capability": "auth",
        "title": "Auth header prose contradicts the working example",
        "doc": "docs_gapped/overview.md",
        "symptom": "The gapped overview presents `Authorization: Bearer` as the canonical "
        "auth method, which the server rejects with 401; the API actually requires the "
        "`X-MemStore-Key` header.",
        "fix": "Corrected the auth prose to `X-MemStore-Key` so it matches the example.",
    },
}

# rule table: API capability -> the gap that explains a failure needing it.
_CAPABILITY_TO_GAP: dict[str, str] = {g["capability"]: gid for gid, g in GAPS.items()}


def attribute_failure(task: dict[str, Any]) -> Optional[str]:
    """Return the gap id responsible for this failed task, or None."""
    # explicit hint on the task wins.
    if task.get("gap") in GAPS:
        return task["gap"]
    cap = task.get("requires")
    gap = _CAPABILITY_TO_GAP.get(cap)
    if gap:
        return gap
    return _llm_judge_fallback(task)


def _llm_judge_fallback(task: dict[str, Any]) -> Optional[str]:
    """Optional LLM-judge fallback; only runs with a live key. Returns None if
    unavailable so the deterministic pipeline stays keyless."""
    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("REPLAY_ONLY") == "1":
        return None
    try:  # pragma: no cover - only exercised with a live key
        import anthropic

        client = anthropic.Anthropic()
        gap_list = "\n".join(f"- {gid}: {g['title']}" for gid, g in GAPS.items())
        msg = client.messages.create(
            model=os.getenv("AGENT_MODEL", "claude-sonnet-4-5"),
            max_tokens=64,
            messages=[
                {
                    "role": "user",
                    "content": f"A developer task failed. Task: {task.get('instruction')}\n"
                    f"Which of these documentation gaps best explains it? Reply with "
                    f"only the gap id.\n{gap_list}",
                }
            ],
        )
        text = msg.content[0].text.strip()
        for gid in GAPS:
            if gid in text:
                return gid
    except Exception:  # noqa: BLE001
        return None
    return None


def score_run(task_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute the aggregate success rate and collect per-failure gap traces."""
    total = len(task_results)
    passed = sum(1 for t in task_results if t["passed"])
    failures = [t for t in task_results if not t["passed"]]
    gap_ids = []
    for t in failures:
        gid = t.get("gap")
        if gid and gid not in gap_ids:
            gap_ids.append(gid)
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "success_rate": round(100.0 * passed / total, 1) if total else 0.0,
        "gaps": [GAPS[g] for g in gap_ids],
    }
