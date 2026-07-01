# paper-rank-proxy

FastAPI journal rank cache proxy for paper-search workflows.

The service keeps EasyScholar credentials on the server side, exposes a small
token-protected HTTP API, and stores normalized journal rank results in SQLite.
It is intended to be called by local MCP tools or other literature-search
clients that should not directly hold an EasyScholar secret key.

## Features

- Single journal lookup by publication name or ISSN.
- Batch journal lookup for candidate paper lists.
- SQLite cache with separate TTLs for successful and negative results.
- Configurable EasyScholar upstream URL and request rate limit.
- Bearer-token protection for rank endpoints.
- Secret-free repository defaults and mockable upstream client for tests.

## Requirements

- Python 3.11 or newer.
- No standalone SQLite server is required. Python includes the `sqlite3`
  standard library module; SQLAlchemy writes to a local SQLite database file.

## Installation

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
```

On Linux or macOS, use:

```bash
source .venv/bin/activate
```

## Configuration

Copy `.env.example` to `.env` and fill in deployment-specific values.

```env
EASYSCHOLAR_SECRET_KEY=
EASYSCHOLAR_API_URL=
RANK_PROXY_TOKEN=
RANK_CACHE_TTL_DAYS=180
RANK_CACHE_NEGATIVE_TTL_DAYS=7
EASYSCHOLAR_RATE_LIMIT_PER_SECOND=2
RANK_PROXY_DATABASE_URL=sqlite:///./data/rank_cache.sqlite3
RANK_BATCH_MAX_SIZE=100
```

Do not commit `.env`, database files, logs, or real tokens.

`EASYSCHOLAR_API_URL` is intentionally configurable because upstream API
contracts may differ between EasyScholar plans or change over time. The default
client sends a `GET` request with `secretKey`, `publicationName`, and `issn`
query parameters.

## Run Locally

```bash
uvicorn app.main:app --reload
```

The service creates SQLite tables automatically during startup.

## Authentication

All rank endpoints require:

```http
Authorization: Bearer <RANK_PROXY_TOKEN>
```

`GET /health` is unauthenticated and returns only non-sensitive service status.

## API

### Health

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "database": "ok",
  "service": "paper-rank-proxy"
}
```

### Single Rank Lookup

```http
GET /rank?publication_name=IEEE%20Transactions%20on%20Power%20Systems
```

or:

```http
GET /rank?issn=0885-8950
```

Example response:

```json
{
  "publication_name": "IEEE Transactions on Power Systems",
  "normalized_name": "ieee transactions on power systems",
  "issn": null,
  "source": "easyscholar",
  "status": "ok",
  "cache_hit": true,
  "fetched_at": "2026-07-01T00:00:00Z",
  "expires_at": "2026-12-28T00:00:00Z",
  "journal_rank": {
    "sci": "Q1",
    "cas_zone": "Engineering 1",
    "cas_small": "Electrical and Electronic Engineering 1",
    "cas_top": true,
    "impact_factor": 8.7,
    "five_year_if": 8.5,
    "ei": true,
    "cscd": null,
    "pku_core": null,
    "cssci": null,
    "esi": "Engineering",
    "warning": null
  },
  "detail": null
}
```

### Batch Rank Lookup

```http
POST /rank/batch
Content-Type: application/json
Authorization: Bearer <RANK_PROXY_TOKEN>
```

```json
{
  "items": [
    {
      "publication_name": "IEEE Transactions on Power Systems"
    },
    {
      "publication_name": "Applied Energy"
    },
    {
      "issn": "0885-8950"
    }
  ],
  "force_refresh": false
}
```

### Force Refresh

```http
POST /rank/refresh
Content-Type: application/json
Authorization: Bearer <RANK_PROXY_TOKEN>
```

```json
{
  "publication_name": "Applied Energy"
}
```

## Database Schema

`journal_rank_cache`

| Column | Purpose |
| --- | --- |
| `lookup_key` | Unique cache key such as `name:applied energy` or `issn:08858950`. |
| `publication_name`, `normalized_name`, `issn` | Normalized lookup metadata. |
| `source`, `status` | Upstream source and lookup result status. |
| `rank_json`, `raw_response_json` | Standardized rank payload and original upstream response. |
| `sci`, `cas_zone`, `cas_small`, `cas_top`, `impact_factor`, `five_year_if`, `ei`, `cscd`, `pku_core`, `cssci`, `esi`, `warning` | Common query/debug fields extracted from `rank_json`. |
| `fetched_at`, `expires_at`, `created_at`, `updated_at` | Cache lifecycle timestamps. |

`rank_query_log`

| Column | Purpose |
| --- | --- |
| `lookup_key` | Lookup key used by the request. |
| `request_type` | `single`, `batch`, or `refresh`. |
| `cache_hit` | Whether the request was served from cache. |
| `status` | Final lookup status. |
| `upstream_status_code`, `error_message` | Upstream diagnostics without secrets. |
| `created_at` | Log timestamp. |

## Testing

```bash
pytest
ruff check .
```

Tests use local SQLite files and do not require real EasyScholar credentials.

## Security

- Keep `EASYSCHOLAR_SECRET_KEY` only on the proxy server.
- Keep `RANK_PROXY_TOKEN` private and rotate it if it is exposed.
- Do not log request URLs containing `secretKey`.
- Do not return upstream credentials in API responses.

## License

MIT
