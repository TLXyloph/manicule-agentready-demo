"""MemStore — a synthetic in-memory document store mock API.

This is the API the Claude tool-use agent is turned loose on. It deliberately
contains three behaviours that the *gapped* docs get wrong, so an agent relying
only on those docs fails a subset of tasks:

  1. Auth is via the ``X-MemStore-Key`` header (gapped docs say Bearer token).
  2. Listing supports a SQL-style ``filter`` query param (gapped docs omit it).
  3. Pagination returns a ``next_cursor`` field (gapped docs omit the field name).

The store is an in-memory dict so it can be cheaply reset between runs.
"""

from __future__ import annotations

import base64
import json
import re
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

# Synthetic demo key — NOT a secret, purely for the local mock.
API_KEY = "ms_live_demo_key_2026"

SEED_PATH = Path(__file__).resolve().parent.parent / "seed" / "documents.json"


# --------------------------------------------------------------------------- #
# In-memory store
# --------------------------------------------------------------------------- #
class MemStore:
    """A tiny document store: collections -> ordered list of documents."""

    def __init__(self) -> None:
        self.collections: dict[str, list[dict[str, Any]]] = {}
        self._counter: int = 0

    def reset(self) -> None:
        self.collections = {}
        self._counter = 0

    def seed(self) -> None:
        """(Re)load the store from the seed fixture."""
        self.reset()
        if not SEED_PATH.exists():
            return
        data = json.loads(SEED_PATH.read_text())
        for coll in data.get("collections", []):
            self.create_collection(coll["name"])
            for doc in coll.get("documents", []):
                self.store_document(
                    coll["name"],
                    content=doc["content"],
                    metadata=doc.get("metadata", {}),
                )

    def create_collection(self, name: str) -> dict[str, Any]:
        if name in self.collections:
            return {"name": name, "created": False}
        self.collections[name] = []
        return {"name": name, "created": True}

    def store_document(
        self, collection: str, content: str, metadata: dict[str, Any]
    ) -> dict[str, Any]:
        if collection not in self.collections:
            raise KeyError(collection)
        self._counter += 1
        doc = {
            "id": f"doc_{self._counter:04d}",
            "content": content,
            "metadata": metadata or {},
        }
        self.collections[collection].append(doc)
        return doc

    def list_documents(
        self,
        collection: str,
        limit: int = 10,
        cursor: Optional[str] = None,
        metadata_filter: Optional[str] = None,
    ) -> dict[str, Any]:
        if collection not in self.collections:
            raise KeyError(collection)
        docs = self.collections[collection]
        if metadata_filter:
            docs = [d for d in docs if _matches_filter(d["metadata"], metadata_filter)]
        offset = _decode_cursor(cursor)
        window = docs[offset : offset + limit]
        next_offset = offset + limit
        next_cursor = _encode_cursor(next_offset) if next_offset < len(docs) else None
        return {
            "documents": window,
            "next_cursor": next_cursor,
            "total": len(docs),
        }


# --------------------------------------------------------------------------- #
# Cursor helpers (opaque base64 offset)
# --------------------------------------------------------------------------- #
def _encode_cursor(offset: int) -> str:
    return base64.urlsafe_b64encode(str(offset).encode()).decode()


def _decode_cursor(cursor: Optional[str]) -> int:
    if not cursor:
        return 0
    try:
        return int(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="invalid cursor") from exc


# --------------------------------------------------------------------------- #
# SQL-style metadata filter parser
# --------------------------------------------------------------------------- #
# Supports:  field op value [AND field op value ...]
# Operators: =, !=, >, <, >=, <=
# Values:    'quoted string' or bare number
_CLAUSE_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*(>=|<=|!=|=|>|<)\s*(.+?)\s*$"
)


def _coerce(raw: str) -> Any:
    raw = raw.strip()
    if (raw.startswith("'") and raw.endswith("'")) or (
        raw.startswith('"') and raw.endswith('"')
    ):
        return raw[1:-1]
    try:
        if "." in raw:
            return float(raw)
        return int(raw)
    except ValueError:
        return raw


def _matches_filter(metadata: dict[str, Any], expr: str) -> bool:
    for clause in re.split(r"\s+AND\s+", expr, flags=re.IGNORECASE):
        m = _CLAUSE_RE.match(clause)
        if not m:
            raise HTTPException(status_code=400, detail=f"bad filter clause: {clause!r}")
        field, op, raw = m.group(1), m.group(2), m.group(3)
        want = _coerce(raw)
        have = metadata.get(field)
        if not _cmp(have, op, want):
            return False
    return True


def _cmp(have: Any, op: str, want: Any) -> bool:
    if op == "=":
        return have == want
    if op == "!=":
        return have != want
    if have is None:
        return False
    try:
        if op == ">":
            return have > want
        if op == "<":
            return have < want
        if op == ">=":
            return have >= want
        if op == "<=":
            return have <= want
    except TypeError:
        return False
    return False


# --------------------------------------------------------------------------- #
# FastAPI router
# --------------------------------------------------------------------------- #
router = APIRouter(prefix="/v1", tags=["memstore"])


class CreateCollectionBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)


class StoreDocumentBody(BaseModel):
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


def _check_auth(x_memstore_key: Optional[str]) -> None:
    if x_memstore_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="missing or invalid X-MemStore-Key header",
        )


def _store(request: Request) -> MemStore:
    return request.app.state.memstore


@router.post("/collections", status_code=201)
def create_collection(
    body: CreateCollectionBody,
    request: Request,
    x_memstore_key: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    _check_auth(x_memstore_key)
    return _store(request).create_collection(body.name)


@router.post("/collections/{collection}/documents", status_code=201)
def store_document(
    collection: str,
    body: StoreDocumentBody,
    request: Request,
    x_memstore_key: Optional[str] = Header(default=None),
) -> dict[str, Any]:
    _check_auth(x_memstore_key)
    try:
        return _store(request).store_document(collection, body.content, body.metadata)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="collection not found") from exc


@router.get("/collections/{collection}/documents")
def list_documents(
    collection: str,
    request: Request,
    x_memstore_key: Optional[str] = Header(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
    filter: Optional[str] = Query(default=None),  # noqa: A002 (SQL-style metadata filter)
) -> dict[str, Any]:
    _check_auth(x_memstore_key)
    try:
        return _store(request).list_documents(
            collection, limit=limit, cursor=cursor, metadata_filter=filter
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="collection not found") from exc
