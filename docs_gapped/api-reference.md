# MemStore — API Reference

All endpoints are under `/v1`. Authenticate as described in the
[overview](./overview.md).

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

| Param   | Type    | Default | Description                          |
| ------- | ------- | ------- | ------------------------------------ |
| `limit` | integer | `10`    | Maximum number of documents to return. |

The response is a JSON object:

```json
{
  "documents": [ { "id": "doc_0001", "content": "...", "metadata": { } } ],
  "total": 24
}
```

`total` is the number of documents in the collection.

> There is currently no way to page past the first `limit` results, and there is
> no server-side metadata querying — fetch documents and inspect their
> `metadata` on the client.
