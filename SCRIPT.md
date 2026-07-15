# AgentReady — 90-second script

> Setup before recording: `make run`, open `http://localhost:8000/?demo` in a
> clean window. No key required (replay mode). The `?demo` flag auto-runs both
> the before and after so the full jump is on screen.

**[0:00–0:12] The hook**

> "Manicule's claim is that with their docs, coding agents go from failing a
> quarter of their tasks to basically zero. I wanted to *see* that number — so I
> built AgentReady: a live agent task-success meter."

**[0:12–0:35] The before**

> "Here's a real Claude tool-use agent, turned loose on a mock API with only the
> docs as context. It runs eight concrete developer tasks. Against the *gapped*
> docs it scores seventy-five percent — two tasks fail." *(point at the red dots)*

**[0:35–0:58] The attribution**

> "And crucially, it tells you *why*. This panel traces each failure to a specific
> doc gap: the SQL-style metadata filter is undocumented, so the agent can't query
> contacts server-side and under-counts. Pagination's `next_cursor` field is
> missing, so it never gets past the first page. This is the exact class of gap
> Manicule found in the Supermemory docs."

**[0:58–1:20] The jump**

> "Now I click 'Apply doc patch'. Same agent, same tasks — but now reading the
> *completed* docs." *(click; meters settle)* "One hundred percent. The score
> jumps twenty-five points and every red task turns green. The gaps are closed."

**[1:20–1:30] The close**

> "That's AgentRel as a metric a customer can watch climb — and every task is
> verified against real API side effects, not the agent's word. It drops straight
> into Manicule's Audit and Code-Verification steps, and it's built around exactly
> the Seed+ API-first startups Manicule already sells to — Supermemory, Greptile,
> Reducto — where 'does the agent get it right from the docs alone' is the whole
> ballgame."

---

### One-liner

> A live 'agent task-success rate' that attributes every failure to a named doc
> gap, then shows the score jump 75% → 100% the instant the gap is patched.
