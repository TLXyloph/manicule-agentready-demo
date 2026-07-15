# AgentReady — a live agent task-success metric for Manicule

> Built for **[Manicule](https://manicule.dev/)** (YC P26) — the AgentRel / AI-native docs studio.

Manicule's marketing claim is sharp: with their docs approach, coding **agents perform with no
errors, versus failing ~25% of the time with other frameworks.** This repo turns that *slogan*
into a **live, reproducible, per-gap-attributed metric.**

**▶ Live demo (no install):** https://claude.ai/code/artifact/4fb63ba8-ae81-4e32-b52f-9fdb1d8b78bb —
a self-contained build (`site/index.html`) that replays the real Claude tool-use run entirely in the
browser, so the 75% → 100% jump is one click away with nothing to boot. The Artifact is private until
shared from its page; if the link asks for access, clone the repo and run `open site/index.html` — the
same file opens directly with no server.

## The magic moment

On one screen, a real Claude tool-use agent is turned loose on a bundled synthetic API
(**MemStore**, a memory/document API loosely echoing Supermemory's shape) and attempts a suite of
concrete developer tasks — reading **only the provided docs** as context.

1. **First run — against `docs_gapped/`** (deliberately missing/contradictory sections): the agent
   scores **~75%**. Three tasks fail. Each failure is traced to a **specific doc gap**
   (e.g. an undocumented SQL-style metadata filter, a wrong auth header, a missing pagination cursor).
2. You click **"Apply doc patch"** — this swaps `docs_gapped/` → `docs_fixed/`, filling exactly
   those gaps.
3. **Re-run:** the same agent now completes the suite at **~100%.** The success-rate number climbs
   live, and every previously-red task flips to green.

Task success is validated by inspecting **real mock-API side effects** — the agent cannot pass by
merely claiming success.

## Quick start

```bash
cp .env.example .env          # add your ANTHROPIC_API_KEY (or run in replay mode)
make run                      # boots mock API + harness + dashboard on http://localhost:8000
```

The dashboard auto-runs the gapped suite on load. Click **Apply doc patch & re-run** to see the
jump. (Append `?demo` to the URL to auto-run both.)

A **deterministic replay mode** (`REPLAY_ONLY=1`, or simply no key set) reproduces the same
before/after result with no live API key, so the demo never flakes.

```bash
make smoke     # keyless: asserts gapped == 75% (3 fail: auth/filter/cursor) and fixed == 100%
make test      # full suite: mock-API unit tests + the end-to-end smoke test
```

## Architecture

```
app/memstore.py   in-memory mock MemStore API (auth, filter, cursor) + OpenAPI (openapi.yaml)
app/agent.py      Claude tool-use loop: reads ONLY docs_<variant>/, one call_api tool, capped turns
app/checkers.py   deterministic per-task checkers — inspect real store side effects, not the agent's word
app/scoring.py    gap-attribution: capability -> named doc gap rule table (+ optional LLM-judge fallback)
app/harness.py    executes each task's calls against a fresh seeded store, checks, scores; live OR replay
app/main.py       FastAPI: /v1 mock API, /api harness endpoints, /static dashboard
tasks/tasks.json  12 concrete NL developer tasks (9 pass / 3 fail on the gapped docs)
docs_gapped/      deliberately missing/contradictory docs   docs_fixed/  the completed docs
replay/*.json     recorded gapped & fixed runs for keyless deterministic replay
static/           vanilla-JS dashboard (meters, task grid, gap-trace panel) served by FastAPI
site/index.html   self-contained static build — same dashboard with run data embedded, no backend
```

The `site/` build embeds the exact deterministic run output (`/api/run/gapped` and `/api/run/fixed`
in replay mode) so it can be hosted anywhere static — GitHub Pages, or the live Artifact link above —
while `static/` + FastAPI drive the full harness (including the live Claude path when a key is set).

Live and replay share one execution path — only the *source* of the API calls differs (Claude vs.
recorded fixture) — so the checker verdicts and success rates are identical either way.

## Why this maps to Manicule

- It is the **AgentRel thesis made measurable**: docs optimized for agents, scored by whether an
  agent actually succeeds — not a vibe, a number that moves on screen.
- The hidden gap in the demo — an **undocumented SQL-style metadata filter** — is a direct nod to
  the Supermemory case study, where Manicule's writer found SQL-based metadata filtering missing
  from the docs by reading the codebase directly, exactly the kind of gap an Agent-Led Audit is
  meant to catch.
- It plugs into Manicule's own **Agent-Led Audit** and **Agent-Led Code Verification** pipeline
  steps: point the harness at a client's docs + API (MemStore here stands in for a real ICP
  target — a Seed+ developer-infrastructure startup like Supermemory, Greptile, or Reducto), and
  get a task-success rate plus the exact gaps that caused each failure, instead of a slogan.
- It gives Manicule's sales motion a receipt for its sharpest claim — "agents perform no errors
  with our approach vs. failing 25% of the time with other frameworks" — by reproducing that exact
  0%-vs-25%-shaped delta live, per gap, against a docs set Manicule itself didn't write.

See [`DEMO_GUIDE.md`](DEMO_GUIDE.md) for the full narrative and [`SCRIPT.md`](SCRIPT.md) for the
90-second walkthrough.

## License

MIT — see [LICENSE](LICENSE). All data is synthetic; no real customer data is used.
