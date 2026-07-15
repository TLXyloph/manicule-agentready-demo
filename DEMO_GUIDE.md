# AgentReady — Demo Guide

This guide walks the full narrative behind the one-screen demo. Everything runs
locally and **works with no Anthropic key** (deterministic replay).

## Setup

```bash
make install      # one-time: venv + deps
make run          # http://localhost:8000
```

No key needed — the harness detects the absence of `ANTHROPIC_API_KEY` (or
`REPLAY_ONLY=1`) and serves recorded runs. With a key set, the same dashboard
drives a live Claude tool-use agent instead.

## The story in three beats

### 1. The claim, made measurable

Manicule's pitch: *agents fail ~25% of tasks with typical docs, ~0% with ours.*
AgentReady turns that into a **live metric**. A real Claude tool-use agent, given
**only** the docs in `docs_gapped/` and a single `call_api` tool, attempts 8
concrete developer tasks against a bundled mock API (**MemStore**).

On load the dashboard auto-runs this "before" suite: **75% (6/8).** Two tasks are
red.

### 2. Every failure is attributed to a doc gap

The right-hand **Gap traces** panel shows *why* each task failed — not a guess, a
rule-based attribution keyed to the API capability the task needed:

| Failing task | Missing capability | Named doc gap |
| --- | --- | --- |
| Count contacts | server-side metadata `filter` | `undocumented-metadata-filter` |
| Paginate every document | `next_cursor` pagination | `missing-pagination-cursor` |

The gapped docs literally omit the `filter` param and the `next_cursor` field
(and contradict themselves on the auth header — the prose says `Bearer`, the
working sample uses `X-MemStore-Key`). The agent, playing by the docs, under-counts
contacts (sees only the first page) and can't page past the first results.

The undocumented SQL-style metadata filter is a direct nod to Manicule's
**Supermemory** case study, where that exact feature was missing from the docs and
documenting it lifted answer success ~30%.

### 3. Apply the patch → the jump

Click **Apply doc patch & re-run.** This swaps `docs_gapped/` → `docs_fixed/`
(the completed docs) and re-runs the identical agent + task suite. The result:
**100% (8/8).** The success-rate meter jumps **+25**, and the two red tasks flip
to green in place. The gap traces move to a "fixed" state showing exactly which
doc section closed each gap.

## Why the score is trustworthy

Task success is judged by **inspecting real mock-API side effects** — did the
collection get created? does the stored invoice exist? — or by comparing the
agent's self-reported count against ground truth recomputed live from the store.
The agent cannot pass by merely *claiming* success. See `app/checkers.py`.

## Verifying it yourself

```bash
make smoke
# asserts: gapped success-rate < 100% with >=2 failures, each attributed to a
# named gap; fixed == 100%; previously-failing tasks turn green. Exits 0, no key.
```

## Where this plugs into Manicule

- **Audit** step: point the harness at a customer's docs + API and get a
  task-success rate plus the precise gaps behind each failure.
- **Code Verification** step: the checkers are exactly the "does the documented
  thing actually work for an agent" gate.
- It's the AgentRel thesis as a number a customer can watch climb.
