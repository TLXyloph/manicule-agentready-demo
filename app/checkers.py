"""Deterministic task checkers.

Each checker inspects the *real* MemStore side effects (for write tasks) or
compares the agent's self-reported answer against ground truth computed live
from the store (for read tasks). Checkers never trust the agent's prose — they
recompute the truth from the store itself.

A checker has signature ``(store, answer) -> (passed: bool, detail: str)``.
"""

from __future__ import annotations

from typing import Any, Callable

from app.memstore import MemStore


def _as_int(answer: Any) -> int | None:
    """Best-effort extract an integer from an agent self-report."""
    if isinstance(answer, bool):
        return None
    if isinstance(answer, int):
        return answer
    if isinstance(answer, float):
        return int(answer)
    if isinstance(answer, str):
        import re

        m = re.search(r"-?\d+", answer.replace(",", ""))
        if m:
            return int(m.group())
    return None


def _workspace(store: MemStore) -> list[dict[str, Any]]:
    return store.collections.get("workspace", [])


# --------------------------------------------------------------------------- #
# Individual checkers
# --------------------------------------------------------------------------- #
def check_create_reports(store: MemStore, answer: Any) -> tuple[bool, str]:
    ok = "reports" in store.collections
    return ok, f"collection 'reports' exists: {ok}"


def check_create_archive(store: MemStore, answer: Any) -> tuple[bool, str]:
    ok = "archive" in store.collections
    return ok, f"collection 'archive' exists: {ok}"


def check_store_invoice(store: MemStore, answer: Any) -> tuple[bool, str]:
    docs = store.collections.get("reports", [])
    hit = [
        d
        for d in docs
        if d["metadata"].get("category") == "invoice"
        and d["metadata"].get("amount") == 4200
    ]
    return bool(hit), f"invoice(amount=4200) docs in 'reports': {len(hit)}"


def check_store_note(store: MemStore, answer: Any) -> tuple[bool, str]:
    docs = store.collections.get("reports", [])
    hit = [d for d in docs if d["metadata"].get("category") == "note"]
    return bool(hit), f"note docs in 'reports': {len(hit)}"


def check_count_total(store: MemStore, answer: Any) -> tuple[bool, str]:
    truth = len(_workspace(store))
    got = _as_int(answer)
    return got == truth, f"reported {got}, truth {truth}"


def check_first_page(store: MemStore, answer: Any) -> tuple[bool, str]:
    truth = min(5, len(_workspace(store)))
    got = _as_int(answer)
    return got == truth, f"reported {got}, truth {truth}"


def check_count_contacts(store: MemStore, answer: Any) -> tuple[bool, str]:
    truth = len([d for d in _workspace(store) if d["metadata"].get("category") == "contact"])
    got = _as_int(answer)
    return got == truth, f"reported {got} contacts, truth {truth}"


def check_collect_all_ids(store: MemStore, answer: Any) -> tuple[bool, str]:
    truth = len(_workspace(store))
    got = _as_int(answer)
    return got == truth, f"reported {got} distinct ids, truth {truth}"


CHECKERS: dict[str, Callable[[MemStore, Any], tuple[bool, str]]] = {
    "create_reports": check_create_reports,
    "create_archive": check_create_archive,
    "store_invoice": check_store_invoice,
    "store_note": check_store_note,
    "count_total": check_count_total,
    "first_page": check_first_page,
    "count_contacts": check_count_contacts,
    "collect_all_ids": check_collect_all_ids,
}


def run_checker(task_id: str, store: MemStore, answer: Any) -> tuple[bool, str]:
    checker = CHECKERS.get(task_id)
    if checker is None:
        return False, f"no checker registered for task {task_id!r}"
    return checker(store, answer)
