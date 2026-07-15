# AgentReady — Demo Guide

Built for **Manicule** (YC P26, founded 2025 by Naman Bansal and Shreyans Jain) — the
"AgentRel" / AI-native technical-docs studio pitching Seed+ developer-tool startups on
*"twice as fast with AI and half the cost of hiring a DevRel."*

This guide covers setup, the tailored narrative, and talking points for a Loom recording.
Everything runs locally and **works with no Anthropic key** (deterministic replay), so the
recording never flakes mid-take.

## Setup

**Fastest (no install):** open the live demo —
https://claude.ai/code/artifact/4fb63ba8-ae81-4e32-b52f-9fdb1d8b78bb. It's a self-contained
build (`site/index.html`) that replays the same run entirely in the browser, so the 75% → 100%
jump is one click away with nothing to boot. The Artifact is private until shared from its page; if
the link asks for access, the same file also opens directly with no server: `open site/index.html`.

**Full harness (local):**

```bash
make install      # one-time: venv + deps
make run          # http://localhost:8000
```

No key needed — the harness detects the absence of `ANTHROPIC_API_KEY` (or
`REPLAY_ONLY=1`) and serves recorded runs. With a key set, the same dashboard drives a
live Claude tool-use agent instead.

## The story in three beats

### 1. The claim, made measurable

Manicule's YC launch page makes a sharp, falsifiable-sounding claim: *"agents perform no
errors while using our approach vs failing 25% of the time with other frameworks."*
AgentReady turns that slogan into a **live metric** instead of asking anyone to take it on
faith. A real Claude tool-use agent, given **only** the docs in `docs_gapped/` and a single
`call_api` tool, attempts 12 concrete developer tasks against a bundled mock API
(**MemStore** — a document/metadata store loosely echoing the shape of Supermemory's Memory
API, one of Manicule's own named case studies).

On load the dashboard auto-runs this "before" suite: **75% (9/12).** Three tasks are red.

### 2. Every failure is attributed to a doc gap

The right-hand **Gap traces** panel shows *why* each task failed — not a guess, a
rule-based attribution keyed to the API capability the task needed:

| Failing task | Missing / contradicted capability | Named doc gap |
| --- | --- | --- |
| Verify API credentials | correct `X-MemStore-Key` auth header | `auth-header-contradiction` |
| Count contacts | server-side metadata `filter` | `undocumented-metadata-filter` |
| Paginate every document | `next_cursor` pagination | `missing-pagination-cursor` |

The gapped docs literally omit the `filter` param and the `next_cursor` field, and
contradict themselves on the auth header — the prose presents `Authorization: Bearer` as
the canonical method, which the server rejects with 401, while the API actually requires
`X-MemStore-Key`. The agent, playing by the docs, fails the credential check, under-counts
contacts (sees only the first page), and can't page past the first results.

The undocumented SQL-style metadata filter is a **direct nod to Manicule's own Supermemory
case study**: the write-up says a Manicule writer had to hand-consult Supermemory's
codebase to discover SQL-based metadata filtering that had been missed entirely from the
existing docs — and documenting it was part of what lifted answer success ~30% in 23 days.
AgentReady stages the exact same failure mode, but scores it automatically instead of
requiring a writer to notice it by hand.

### 3. Apply the patch → the jump

Click **Apply doc patch & re-run.** This swaps `docs_gapped/` → `docs_fixed/` (the
completed docs) and re-runs the identical agent + task suite. The result: **100% (12/12).**
The success-rate meter jumps **+25**, and the three red tasks flip to green in place. The gap
traces move to a "fixed" state showing exactly which doc section closed each gap.

That +25-point jump is the number on Manicule's own YC page, reproduced live instead of
asserted in marketing copy: 0% agent error rate with complete docs vs. ~25% without.

## Why the score is trustworthy

Task success is judged by **inspecting real mock-API side effects** — did the collection
get created? does the stored invoice exist? — or by comparing the agent's self-reported
count against ground truth recomputed live from the store. The agent cannot pass by merely
*claiming* success. See `app/checkers.py`.

## Verifying it yourself

```bash
make smoke
# asserts: gapped success-rate == 75% with exactly 3 failures (auth/filter/cursor),
# each attributed to a named gap; fixed == 100%; previously-failing tasks turn
# green. Exits 0, no key.
```

## Where this plugs into Manicule

- **Audit** step: point the harness at a customer's docs + API and get a task-success rate
  plus the precise gaps behind each failure — the same "agent-led audit" Manicule already
  sells, made into a number instead of a report.
- **Agent-Led Code Verification** step: the checkers are exactly the "does the documented
  thing actually work for an agent" gate Manicule's 7-step pipeline already promises.
- **Sales / ICP fit**: Manicule sells to Seed+ API-first dev-tool startups (Greptile,
  Reducto, Rootly, PromptLayer, Skyvern, Supermemory) who live and die by whether a coding
  agent can correctly call their API from the docs alone — this harness is a proof-of-value
  a Manicule AE could literally run live on a prospect's own docs before closing.

## Talking points for a Loom recording (~90 seconds)

Suggested beats, timestamped for a screen recording of the dashboard:

1. **(0:00-0:15) Hook.** "Manicule's pitch is that with their docs, agents perform with
   *no errors* — versus failing 25% of the time with typical docs. That's a strong claim.
   I built a harness that actually measures it, live, on camera."
2. **(0:15-0:35) Show the before state.** Load the dashboard, point at the **75% (9/12)**
   meter and the three red tasks. "This is a real Claude agent, given only the docs — nothing
   else — trying to do 12 real developer tasks against a live mock API called MemStore. Three
   fail."
3. **(0:35-0:55) Show the gap trace.** Click into the failing tasks. "It's not just
   pass/fail — the harness tells you *why*: this docs set never mentions the metadata
   `filter` param, so the agent can't count contacts correctly. That's the same class of
   gap Manicule's own Supermemory case study found by hand — an undocumented SQL-style
   filter buried in the codebase."
4. **(0:55-1:15) The patch and the jump.** Click **Apply doc patch & re-run**. "Now I swap
   in the complete docs and re-run the identical agent on the identical tasks." Watch the
   meter climb to **100% (12/12)** and the red tasks flip green. "That's Manicule's 0%-vs-25%
   number, reproduced live instead of asserted in a launch post."
5. **(1:15-1:30) Close.** "Everything here — the mock API, the docs, the task suite — is
   synthetic and runs locally with no API key, so it's safe to demo on any prospect's call.
   This is exactly the kind of proof-of-value I'd want an AE at Manicule to be able to pull
   up mid-pitch, or a Content Engineer to wire into the audit product. Repo's linked below."

Optional add-on line if asked about ICP: "This is built around the shape of the customers
Manicule already lists — Supermemory, Greptile, Reducto — API-first dev-tool startups
where 'does the agent get it right from the docs alone' is the whole ballgame."

## Known gaps (be upfront if asked)

- Screenshots in `evidence/` were captured via headless Chrome (the browser extension
  wasn't connected at capture time); the dashboard renders identically either way.
- The captured PNGs show the success meter mid count-up animation, not the settled
  75%/100% values — the settled numbers are confirmed via `/api/run/gapped` and
  `/api/run/fixed` directly.
- This walkthrough and the smoke test were verified in replay mode
  (`REPLAY_ONLY=1`, no live `ANTHROPIC_API_KEY`); the live Claude tool-use path exists and
  is code-identical to replay, but wasn't exercised end-to-end for this recording.
