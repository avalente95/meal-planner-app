import pytest
from fastapi.testclient import TestClient

import backend.app.main as main

ALWAYS = {
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
}
NON_DEV_ONLY = {
    "Strict-Transport-Security": "max-age=31536000",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}

REQUESTS = [
    ("/health", 200),
    ("/api/v1/recipes", 401),
    ("/api/v1/ingredients", 401),
    ("/questa-route-non-esiste", 404),
]


@pytest.fixture
def client():
    return TestClient(main.app)


def set_env(monkeypatch, value):
    monkeypatch.setattr(main, "ENVIRONMENT", value)


@pytest.mark.parametrize("path,expected_status", REQUESTS)
def test_production_has_all_headers(client, monkeypatch, path, expected_status):
    set_env(monkeypatch, "production")
    r = client.get(path)
    assert r.status_code == expected_status
    for name, value in {**ALWAYS, **NON_DEV_ONLY}.items():
        assert r.headers.get(name) == value, f"{name} errato o mancante su {path}"


@pytest.mark.parametrize("path,expected_status", REQUESTS)
def test_development_skips_hsts_and_csp(client, monkeypatch, path, expected_status):
    set_env(monkeypatch, "development")
    r = client.get(path)
    assert r.status_code == expected_status
    for name, value in ALWAYS.items():
        assert r.headers.get(name) == value, f"{name} errato o mancante su {path}"
    for name in NON_DEV_ONLY:
        assert name not in r.headers, f"{name} non deve comparire in development"


@pytest.mark.parametrize("env", ["staging", "prod", "Production", ""])
def test_any_non_development_env_gets_all_headers(client, monkeypatch, env):
    set_env(monkeypatch, env)
    r = client.get("/health")
    for name in NON_DEV_ONLY:
        assert name in r.headers, f"{name} assente con ENVIRONMENT={env!r}"


def test_wrong_key_401_has_headers(client, monkeypatch):
    set_env(monkeypatch, "production")
    r = client.get("/api/v1/recipes", headers={"X-API-Key": "chiave-sbagliata"})
    assert r.status_code == 401
    for name, value in {**ALWAYS, **NON_DEV_ONLY}.items():
        assert r.headers.get(name) == value


@pytest.fixture
def boom_route():
    async def boom():
        raise RuntimeError("boom")

    main.app.add_api_route("/__boom", boom)
    yield
    main.app.router.routes = [
        r for r in main.app.router.routes if getattr(r, "path", None) != "/__boom"
    ]


@pytest.mark.xfail(strict=True, reason="Limite noto: 500 senza header, fix in W10 (SEC-16)")
def test_unhandled_500_has_headers(boom_route, monkeypatch):
    set_env(monkeypatch, "production")
    c = TestClient(main.app, raise_server_exceptions=False)
    r = c.get("/__boom")
    assert r.status_code == 500
    for name, value in {**ALWAYS, **NON_DEV_ONLY}.items():
        assert r.headers.get(name) == value