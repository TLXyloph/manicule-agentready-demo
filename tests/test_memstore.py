"""Unit tests for the MemStore mock API — the three gap-relevant behaviours."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.memstore import API_KEY

AUTH = {"X-MemStore-Key": API_KEY}


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def test_healthz(client):
    assert client.get("/healthz").json() == {"status": "ok"}


def test_seed_loaded(client):
    r = client.get("/v1/collections/workspace/documents", params={"limit": 100}, headers=AUTH)
    assert r.status_code == 200
    assert r.json()["total"] == 24


def test_auth_required_and_correct_header(client):
    # No header -> 401
    assert client.get("/v1/collections/workspace/documents").status_code == 401
    # Wrong scheme (Bearer, the gapped-docs mistake) -> 401
    r = client.get(
        "/v1/collections/workspace/documents",
        headers={"Authorization": "Bearer " + API_KEY},
    )
    assert r.status_code == 401
    # Correct header -> 200
    assert client.get("/v1/collections/workspace/documents", headers=AUTH).status_code == 200


def test_sql_style_metadata_filter(client):
    r = client.get(
        "/v1/collections/workspace/documents",
        params={"filter": "category = 'invoice' AND amount > 1000", "limit": 100},
        headers=AUTH,
    )
    docs = r.json()["documents"]
    assert docs, "expected some invoices over 1000"
    assert all(d["metadata"]["category"] == "invoice" and d["metadata"]["amount"] > 1000 for d in docs)


def test_cursor_pagination(client):
    seen: list[str] = []
    cursor = None
    for _ in range(20):  # safety cap
        params = {"limit": 5}
        if cursor:
            params["cursor"] = cursor
        page = client.get("/v1/collections/workspace/documents", params=params, headers=AUTH).json()
        seen.extend(d["id"] for d in page["documents"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert len(seen) == 24
    assert len(set(seen)) == 24  # no duplicates across pages


def test_create_and_store_roundtrip(client):
    assert client.post("/v1/collections", json={"name": "scratch"}, headers=AUTH).status_code == 201
    r = client.post(
        "/v1/collections/scratch/documents",
        json={"content": "hello", "metadata": {"category": "note"}},
        headers=AUTH,
    )
    assert r.status_code == 201
    assert r.json()["id"].startswith("doc_")
