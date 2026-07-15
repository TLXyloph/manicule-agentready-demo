# MemStore — API Reference

All endpoints are under `/v1`. Authenticate with the `X-MemStore-Key` header as
described in the [overview](./overview.md).

## Create a collection

`POST /v1/collections`

Body: `{"name": "<collection-name>"}` → `201` with `{"name", "created"}`.

## Store a document

`POST /v1/collections/{collection}/documents`

Body: `{"content": "<text>", "metadata": { ... }}` → `201` with the stored
document `{"id", "content", "metadata"}`.

## List documents

`GET /v1/collections/{collection}/documents`

Query parameters:

| Param    | Type    | Default | Description                                            |
| -------- | ------- | ------- | ------------------------------------------------------ |
| `limit`  | integer | `10`    | Maximum number of documents to return (max 100).       |
| `cursor` | string  | —       | Opaque cursor from a previous response's `next_cursor`. |
| `filter` | string  | —       | SQL-style metadata filter (see below).                  |

### Pagination with `next_cursor`

Each response includes a **`next_cursor`** field. To page through every document,
pass it back as the `cursor` query parameter until `next_cursor` is `null`:

```bash
# page 1
curl ".../documents?limit=10" -H "X-MemStore-Key: ms_live_demo_key_2026"
# -> { "documents": [...], "next_cursor": "MTA=", "total": 24 }

# page 2
curl ".../documents?limit=10&cursor=MTA=" -H "X-MemStore-Key: ms_live_demo_key_2026"
```

### SQL-style metadata filtering with `filter`

Pass a `filter` expression to query metadata **server-side** instead of fetching
and scanning on the client:

```
filter=category = 'contact'
filter=category = 'invoice' AND amount > 1000
```

Supported operators: `=`, `!=`, `>`, `<`, `>=`, `<=`, joined with `AND`. String
values are single-quoted; numbers are bare. Example:

```bash
curl --get ".../documents" \
  --data-urlencode "filter=category = 'invoice' AND status = 'paid'" \
  -H "X-MemStore-Key: ms_live_demo_key_2026"
```

### Response shape

```json
{
  "documents": [ { "id": "doc_0001", "content": "...", "metadata": { } } ],
  "next_cursor": "MTA=",
  "total": 24
}
```

`total` is the count of documents matching the filter (or the whole collection
when no filter is given). `next_cursor` is `null` on the last page.
