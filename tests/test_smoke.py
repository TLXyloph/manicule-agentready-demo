"""Smoke test for the AgentReady magic moment.

Runs the full pipeline in deterministic replay mode (NO Anthropic key required)
and asserts the before/after jump:

  * gapped docs  -> success rate strictly < 100% with at least 2 failing tasks,
    every failure attributed to a named doc gap;
  * fixed docs   -> 100%, with the previously-failing tasks now green.

Must exit 0 with no ANTHROPIC_API_KEY set.
"""

from __future__ import annotations

import os

import pytest

from app.harness import run_suite
from app.scoring import GAPS


@pytest.fixture(autouse=True)
def _replay_env(monkeypatch):
    # Force keyless replay regardless of the developer's environment.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("REPLAY_ONLY", "1")


def test_gapped_run_scores_below_100():
    result = run_suite("gapped")
    assert result["mode"] == "replay"
    assert result["success_rate"] < 100.0, "gapped docs should not be a perfect run"
    assert result["failed"] >= 2, "expected at least 2 tasks to fail on gapped docs"


def test_every_gapped_failure_is_attributed_to_a_named_gap():
    result = run_suite("gapped")
    failures = [t for t in result["tasks"] if not t["passed"]]
    assert failures, "expected failures on gapped docs"
    for t in failures:
        assert t["gap"] in GAPS, f"failure {t['id']} not attributed to a named gap"
    # the run-level summary surfaces those gaps for the dashboard trace panel.
    assert result["gaps"], "expected gap traces in the summary"


def test_fixed_run_scores_100_and_flips_failures_green():
    gapped = run_suite("gapped")
    fixed = run_suite("fixed")
    assert fixed["success_rate"] == 100.0, "fixed docs should be a perfect run"
    assert fixed["failed"] == 0

    gapped_failures = {t["id"] for t in gapped["tasks"] if not t["passed"]}
    fixed_by_id = {t["id"]: t for t in fixed["tasks"]}
    assert gapped_failures, "sanity: there were failures to flip"
    for tid in gapped_failures:
        assert fixed_by_id[tid]["passed"], f"task {tid} did not turn green after the patch"


def test_before_after_jump_is_positive():
    gapped = run_suite("gapped")
    fixed = run_suite("fixed")
    assert fixed["success_rate"] > gapped["success_rate"]


def test_runs_without_api_key():
    assert not os.getenv("ANTHROPIC_API_KEY")
    run_suite("gapped")  # must not raise
    run_suite("fixed")
