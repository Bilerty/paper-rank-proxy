# Security Policy

## Reporting a Vulnerability

Please report security issues privately to the repository owner. Do not open a
public issue containing tokens, EasyScholar credentials, server logs with
secrets, or private deployment details.

## Secret Handling

- `EASYSCHOLAR_SECRET_KEY` belongs only on the deployed proxy server.
- `RANK_PROXY_TOKEN` protects client access to rank endpoints.
- `.env`, SQLite database files, and logs are excluded by `.gitignore`.
- Tests must use fake credentials and mocked upstream responses.
