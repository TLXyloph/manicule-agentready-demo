# AgentReady — a live agent task-success metric for Manicule

> Built for **[Manicule](https://manicule.dev/)** (YC P26) — the AgentRel / AI-native docs studio.

Manicule's marketing claim is sharp: with their docs approach, coding **agents perform with no
errors, versus failing ~25% of the time with other frameworks.** This repo turns that *slogan*
into a **live, reproducible, per-gap-attributed metric.**

## The magic moment

On one screen, a real Claude tool-use agent is turned loose on a bundled synthetic API
(**MemStore**, a memory/document API loosely echoing Supermemory's shape) and attempts a suite of
concrete developer tasks — reading **only the provided docs** as context.

1. **First run — against `docs_gapped/`** (deliberately missing/contradictory sections): the agent
   scores **~70-80%**. At least two tasks fail. Each failure is traced to a **specific doc gap**
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

Open http://localhost:8000, click **Run (gapped)**, then **Apply doc patch & re-run**.

A **deterministic replay mode** (`REPLAY_ONLY=1`) reproduces the same before/after result with no
live API key, so the demo never flakes.

## Why this maps to Manicule

- It is the **AgentRel thesis made measurable**: docs optimized for agents, scored by whether an
  agent actually succeeds.
- The hidden gap in the demo — an **undocumented SQL-style metadata filter** — is a direct nod to
  the Supermemory case study, where Manicule found SQL-based metadata filtering missing from the docs.
- It plugs into Manicule's **Audit** and **Code Verification** pipeline steps: point the harness at
  docs + API, get a task-success rate and the exact gaps that caused each failure.

See [`DEMO_GUIDE.md`](DEMO_GUIDE.md) for the full narrative and [`SCRIPT.md`](SCRIPT.md) for the
90-second walkthrough.

## License

MIT — see [LICENSE](LICENSE). All data is synthetic; no real customer data is used.
