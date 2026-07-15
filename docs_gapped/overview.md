# MemStore — Overview

MemStore is a tiny document store. Documents live in named **collections** and
carry arbitrary JSON **metadata**.

Base URL: `http://localhost:8000`

## Authentication

Every request must be authenticated. Pass your API key as a **Bearer token** in
the `Authorization` header:

```
Authorization: Bearer ms_live_demo_key_2026
```

> Note: the code samples below use a different header — copy the samples, they
> are the source of truth for what the server actually accepts.

## Quickstart

Create a collection:

```bash
curl -X POST http://localhost:8000/v1/collections \
  -H "X-MemStore-Key: ms_live_demo_key_2026" \
  -H "Content-Type: application/json" \
  -d '{"name": "reports"}'
```

Store a document with metadata:

```bash
curl -X POST http://localhost:8000/v1/collections/reports/documents \
  -H "X-MemStore-Key: ms_live_demo_key_2026" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello", "metadata": {"category": "note"}}'
```

List documents in a collection:

```bash
curl http://localhost:8000/v1/collections/reports/documents?limit=10 \
  -H "X-MemStore-Key: ms_live_demo_key_2026"
```

See the [API reference](./api-reference.md) for the full endpoint list.
