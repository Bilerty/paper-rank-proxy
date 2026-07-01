# Contributing

Thanks for improving `paper-rank-proxy`.

## Development

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -e ".[dev]"
pytest
ruff check .
```

Use environment variables or a local `.env` file for secrets. Never commit real
API keys, bearer tokens, SQLite database files, or logs.

## Pull Request Checklist

- Add or update tests for behavior changes.
- Keep API responses backward-compatible when possible.
- Avoid logging full upstream URLs because EasyScholar credentials may be query
  parameters.
- Update `README.md` if configuration, endpoints, or schema fields change.
