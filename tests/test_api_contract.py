def test_health_is_public(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_rank_requires_bearer_token(client):
    response = client.get("/rank", params={"publication_name": "Applied Energy"})

    assert response.status_code == 401


def test_rank_rejects_invalid_token(client):
    response = client.get(
        "/rank",
        params={"publication_name": "Applied Energy"},
        headers={"Authorization": "Bearer wrong"},
    )

    assert response.status_code == 403


def test_rank_returns_configuration_error_without_upstream_credentials(client, auth_headers):
    response = client.get(
        "/rank",
        params={"publication_name": "Applied Energy"},
        headers=auth_headers,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "configuration_error"
    assert payload["cache_hit"] is False
    assert payload["journal_rank"] is None


def test_batch_enforces_max_size(client, auth_headers):
    response = client.post(
        "/rank/batch",
        json={"items": [{"publication_name": f"Journal {index}"} for index in range(11)]},
        headers=auth_headers,
    )

    assert response.status_code == 413
