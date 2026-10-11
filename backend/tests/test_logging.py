import json

import structlog
from fastapi.testclient import TestClient

from app.logging_config import configure_logging
from app.main import app


def _request_logs(out: str) -> list[dict]:
    lines = [json.loads(l) for l in out.splitlines() if l.startswith("{")]
    return [l for l in lines if l.get("event") == "request"]


def test_request_log_fields_and_no_leak(capsys):
    structlog.reset_defaults()
    configure_logging("production", "INFO")
    client = TestClient(app)

    response = client.get(
        "/health?token=QUERYSECRET",
        headers={"Authorization": "Bearer HEADERSECRET", "X-API-Key": "KEYSECRET"},
    )
    out = capsys.readouterr().out

    for secret in ("QUERYSECRET", "HEADERSECRET", "KEYSECRET"):
        assert secret not in out

    logs = _request_logs(out)
    assert len(logs) == 1
    entry = logs[0]
    assert entry["method"] == "GET"
    assert entry["route"] == "/health"
    assert entry["status"] == 200
    assert "duration_ms" in entry

    assert entry["request_id"] == response.headers["X-Request-ID"]


def test_unmatched_route_does_not_log_raw_path(capsys):
    structlog.reset_defaults()
    configure_logging("production", "INFO")
    client = TestClient(app)

    client.get("/non-esiste-ATTACKERINPUT")
    out = capsys.readouterr().out

    assert "ATTACKERINPUT" not in out
    logs = _request_logs(out)
    assert logs[0]["route"] == "unmatched"
    assert logs[0]["status"] == 404