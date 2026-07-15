"use strict";

const $ = (s) => document.querySelector(s);
const state = { tasks: [], gapped: null, fixed: null };

async function getJSON(url, opts) {
  const r = await fetch(url, opts);
  if (!r.ok) throw new Error(`${url} -> ${r.status}`);
  return r.json();
}

function setStatus(msg) { $("#status").textContent = msg || ""; }

function animatePct(el, target) {
  el.textContent = target + "%"; // settle immediately so the value is always correct
  const reduce = window.matchMedia && matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reduce) return;
  const start = 0, dur = 700, t0 = performance.now();
  function step(now) {
    const k = Math.min(1, (now - t0) / dur);
    el.textContent = Math.round(start + (target - start) * k) + "%";
    if (k < 1) requestAnimationFrame(step);
    else el.textContent = target + "%";
  }
  requestAnimationFrame(step);
}

function renderMeter(which, result) {
  const m = $(`#meter-${which}`);
  animatePct(m.querySelector("[data-pct]"), result.success_rate);
  m.querySelector("[data-passed]").textContent = result.passed;
  m.querySelector("[data-total]").textContent = result.total;
  m.classList.remove("faded");
  m.classList.add("active");
}

function buildTaskGrid() {
  const ul = $("#task-grid");
  ul.innerHTML = "";
  for (const t of state.tasks) {
    const li = document.createElement("li");
    li.className = "task";
    li.id = `task-${t.id}`;
    li.innerHTML = `
      <div class="dots">
        <span class="dot" data-variant="gapped"></span>
        <span class="dot" data-variant="fixed"></span>
      </div>
      <span class="task-title">${t.title}</span>
      <span class="task-req">${t.requires}</span>`;
    ul.appendChild(li);
  }
}

function paintDots(which, result) {
  for (const t of result.tasks) {
    const dot = document.querySelector(`#task-${t.id} .dot[data-variant="${which}"]`);
    if (!dot) continue;
    dot.classList.remove("pass", "fail");
    dot.classList.add(t.passed ? "pass" : "fail");
    if (which === "fixed") {
      const wasFail = state.gapped && !state.gapped.tasks.find((x) => x.id === t.id)?.passed;
      if (wasFail && t.passed) $(`#task-${t.id}`).classList.add("flip");
    }
  }
}

function renderTraces(result, patched) {
  const box = $("#gap-traces");
  const failures = result.tasks.filter((t) => !t.passed);
  if (patched) {
    // show the previously-failing traces as resolved
    const prev = state.gapped ? state.gapped.tasks.filter((t) => !t.passed) : [];
    if (!prev.length) { box.innerHTML = `<p class="empty">No gaps — perfect run.</p>`; return; }
    box.innerHTML = prev.map((t) => traceCard(t, true)).join("");
    return;
  }
  if (!failures.length) { box.innerHTML = `<p class="empty">No failures — nothing to attribute.</p>`; return; }
  box.innerHTML = failures.map((t) => traceCard(t, false)).join("");
}

const GAP_META = {}; // filled from run summary
function traceCard(task, patched) {
  const g = GAP_META[task.gap] || { title: task.gap, symptom: "", doc: "", fix: "" };
  return `
    <div class="trace ${patched ? "patched" : ""}">
      <div class="task-ref">${patched ? "✓ fixed" : "✗ failed"} · ${task.title}</div>
      <h3>${g.title}</h3>
      <p>${g.symptom}</p>
      <p class="doc">${g.doc}</p>
      ${patched ? `<p class="fix">↳ ${g.fix}</p>` : `<p>Agent reported: <b>${fmt(task.answer)}</b> (expected ${fmt(task.expected)})</p>`}
    </div>`;
}
function fmt(v) { return typeof v === "string" && v.length > 24 ? v.slice(0, 24) + "…" : String(v); }

function indexGaps(result) { for (const g of result.gaps) GAP_META[g.id] = g; }

async function runGapped() {
  setStatus("Agent running against gapped docs…");
  $("#btn-gapped").disabled = true;
  const res = await getJSON("/api/run/gapped", { method: "POST" });
  state.gapped = res;
  indexGaps(res);
  renderMeter("gapped", res);
  paintDots("gapped", res);
  renderTraces(res, false);
  $("#btn-fixed").disabled = false;
  setStatus(`Gapped: ${res.passed}/${res.total} pass · ${res.gaps.length} doc gap(s) found · mode=${res.mode}`);
}

async function runFixed() {
  setStatus("Applying doc patch and re-running…");
  $("#btn-fixed").disabled = true;
  const res = await getJSON("/api/run/fixed", { method: "POST" });
  state.fixed = res;
  renderMeter("fixed", res);
  paintDots("fixed", res);
  renderTraces(res, true);
  const jump = Math.round(res.success_rate - (state.gapped?.success_rate ?? 0));
  $("#delta-num").textContent = (jump >= 0 ? "+" : "") + jump;
  setStatus(`Fixed: ${res.passed}/${res.total} pass · every previously-failing task turned green.`);
}

function reset() {
  state.gapped = state.fixed = null;
  for (const w of ["gapped", "fixed"]) {
    const m = $(`#meter-${w}`);
    m.classList.add("faded"); m.classList.remove("active");
    m.querySelector("[data-pct]").textContent = "—";
    m.querySelector("[data-passed]").textContent = "–";
    m.querySelector("[data-total]").textContent = "–";
  }
  $("#delta-num").textContent = "+0";
  $("#gap-traces").innerHTML = `<p class="empty">Run the gapped suite to reveal the doc gaps behind each failure.</p>`;
  buildTaskGrid();
  $("#btn-gapped").disabled = false;
  $("#btn-fixed").disabled = true;
  setStatus("");
}

async function init() {
  try {
    const cfg = await getJSON("/api/config");
    $("#mode-badge").textContent = `${cfg.mode} · ${cfg.model}`;
    const { tasks } = await getJSON("/api/tasks");
    state.tasks = tasks;
    buildTaskGrid();
    $("#btn-gapped").onclick = runGapped;
    $("#btn-fixed").onclick = runFixed;
    $("#btn-reset").onclick = reset;
    await runGapped(); // auto-run the "before" so the gaps are visible on load
    if (location.search.includes("demo")) await runFixed(); // full before/after for demos
  } catch (e) {
    setStatus("Error: " + e.message);
  }
}

init();
