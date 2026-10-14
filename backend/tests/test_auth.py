import base64
import json
import os
import re
import time
import uuid

os.environ.setdefault("SUPABASE_URL", "https://test.supabase.co")

import jwt  # noqa: E402
import pytest  # noqa: E402
from cryptography.hazmat.primitives.asymmetric import ec  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import auth  # noqa: E402
from app.main import app  # noqa: E402

ME = "/api/v1/me"
client = TestClient(app)


@pytest.fixture(scope="module")
def private_key():
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture(scope="module")
def other_key():
    return ec.generate_private_key(ec.SECP256R1())


class FakeSigningKey:
    def __init__(self, key):
        self.key = key


class FakeJWKSClient:
    def __init__(self, public_key):
        self._public_key = public_key

    def get_signing_key_from_jwt(self, token):
        return FakeSigningKey(self._public_key)


@pytest.fixture(autouse=True)
def fake_jwks(monkeypatch, private_key):
    monkeypatch.setattr(
        auth, "get_jwks_client", lambda: FakeJWKSClient(private_key.public_key())
    )


class RecordingLogger:

    def __init__(self):
        self.events = []

    def warning(self, event, **kwargs):
        self.events.append((event, kwargs))


@pytest.fixture
def recorded_logs(monkeypatch):
    rec = RecordingLogger()
    monkeypatch.setattr(auth, "logger", rec)
    return rec


def build_claims(**overrides):
    now = int(time.time())
    claims = {
        "sub": str(uuid.uuid4()),
        "aud": "authenticated",
        "iss": auth.ISSUER,
        "iat": now,
        "exp": now + 3600,
    }
    claims.update(overrides)
    return {k: v for k, v in claims.items() if v is not None}


def sign(claims, key, algorithm="ES256"):
    return jwt.encode(claims, key, algorithm=algorithm, headers={"kid": "test-key"})


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def tamper_sub(token: str, new_sub: str) -> str:
    """Cambia il sub nel payload mantenendo la firma originale."""
    header, payload, signature = token.split(".")
    claims = json.loads(_b64url_decode(payload))
    claims["sub"] = new_sub
    return ".".join([header, _b64url(json.dumps(claims).encode()), signature])


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}



def test_verify_token_valid(private_key):
    sub = uuid.uuid4()
    token = sign(build_claims(sub=str(sub)), private_key)
    assert auth.verify_token(token) == sub


def _expired(key, other):
    return sign(build_claims(exp=int(time.time()) - 10), key)


def _wrong_aud(key, other):
    return sign(build_claims(aud="altro"), key)


def _wrong_iss(key, other):
    return sign(build_claims(iss="https://evil.example/auth/v1"), key)


def _no_exp(key, other):
    return sign(build_claims(exp=None), key)


def _no_sub(key, other):
    return sign(build_claims(sub=None), key)


def _no_aud(key, other):
    return sign(build_claims(aud=None), key)


def _no_iss(key, other):
    return sign(build_claims(iss=None), key)


def _sub_not_uuid(key, other):
    return sign(build_claims(sub="non-un-uuid"), key)


def _other_key(key, other):
    return sign(build_claims(), other)


def _hs256(key, other):
    return sign(build_claims(), "x" * 64, algorithm="HS256")


def _alg_none(key, other):
    return jwt.encode(build_claims(), None, algorithm="none")


def _tampered(key, other):
    return tamper_sub(sign(build_claims(), key), str(uuid.uuid4()))


def _garbage(key, other):
    return "abc"


def _empty(key, other):
    return ""


INVALID_TOKENS = [
    pytest.param(_expired, "ExpiredSignatureError", id="scaduto"),
    pytest.param(_wrong_aud, "InvalidAudienceError", id="aud-sbagliato"),
    pytest.param(_wrong_iss, "InvalidIssuerError", id="iss-sbagliato"),
    pytest.param(_no_exp, "MissingRequiredClaimError", id="senza-exp"),
    pytest.param(_no_sub, "MissingRequiredClaimError", id="senza-sub"),
    pytest.param(_no_aud, "MissingRequiredClaimError", id="senza-aud"),
    pytest.param(_no_iss, "MissingRequiredClaimError", id="senza-iss"),
    pytest.param(_sub_not_uuid, "ValueError", id="sub-non-uuid"),
    pytest.param(_other_key, "InvalidSignatureError", id="chiave-diversa"),
    pytest.param(_hs256, "InvalidAlgorithmError", id="alg-HS256"),
    pytest.param(_alg_none, "InvalidAlgorithmError", id="alg-none"),
    pytest.param(_tampered, "InvalidSignatureError", id="payload-manomesso"),
    pytest.param(_garbage, "DecodeError", id="spazzatura"),
    pytest.param(_empty, "DecodeError", id="vuoto"),
]


@pytest.mark.parametrize("make, expected_reason", INVALID_TOKENS)
def test_verify_token_rejects_invalid(make, expected_reason, private_key, other_key):
    token = make(private_key, other_key)
    with pytest.raises(auth.AuthError) as exc_info:
        auth.verify_token(token)
    assert str(exc_info.value) == expected_reason


# --------------------------------------------------------------------------
# Endpoint /api/v1/me: il wrapper FastAPI
# --------------------------------------------------------------------------
def test_me_with_valid_token(private_key):
    sub = str(uuid.uuid4())
    response = client.get(ME, headers=auth_header(sign(build_claims(sub=sub), private_key)))
    assert response.status_code == 200
    assert sub in response.text


def _failing_requests(private_key, other_key):
    """Tutte le richieste che devono dare 401, come (headers)."""
    tokens = [make(private_key, other_key) for make in (
        _expired, _wrong_aud, _wrong_iss, _no_exp, _no_sub, _sub_not_uuid,
        _other_key, _hs256, _alg_none, _tampered, _garbage,
    )]
    return [
        {},  
        {"Authorization": "Basic YWJjOmRlZg=="},  
        {"Authorization": "Bearer"}, 
        {"Authorization": "Bearer "},
        *[auth_header(t) for t in tokens if t],
    ]


def test_me_rejects_all_invalid_with_401(private_key, other_key):
    for headers in _failing_requests(private_key, other_key):
        response = client.get(ME, headers=headers)
        assert response.status_code == 401, headers
        assert response.headers.get("www-authenticate") == "Bearer", headers


def test_401_responses_are_all_identical(private_key, other_key):
    """Nessun dettaglio sul motivo del rifiuto deve arrivare al client."""
    seen = set()
    for headers in _failing_requests(private_key, other_key):
        response = client.get(ME, headers=headers)
        seen.add(
            (response.status_code, response.text, response.headers.get("www-authenticate"))
        )
    assert len(seen) == 1, seen


# --------------------------------------------------------------------------
# Log: il motivo c'è, il token no
# --------------------------------------------------------------------------
def test_failure_reason_is_logged_without_token(recorded_logs, private_key):
    expired = sign(build_claims(exp=int(time.time()) - 10), private_key)

    client.get(ME)  # nessun header
    client.get(ME, headers=auth_header(expired))

    assert recorded_logs.events == [
        ("auth_failed", {"reason": "missing_credentials"}),
        ("auth_failed", {"reason": "ExpiredSignatureError"}),
    ]
    assert expired not in repr(recorded_logs.events)


def test_success_does_not_log_failures(recorded_logs, private_key):
    client.get(ME, headers=auth_header(sign(build_claims(), private_key)))
    assert recorded_logs.events == []


# --------------------------------------------------------------------------
# Protezione di TUTTE le rotte sotto /api/v1 (anche quelle future)
# --------------------------------------------------------------------------
def _protected_routes():
    """Rotte lette dallo schema OpenAPI: funziona con qualsiasi versione di FastAPI
    e anche quando /docs e /openapi.json sono disattivati (app.openapi() resta chiamabile)."""
    http_methods = {"get", "post", "put", "patch", "delete"}
    routes = []
    for path, operations in app.openapi()["paths"].items():
        if not path.startswith("/api/v1/"):
            continue
        concrete_path = re.sub(r"\{[^}]+\}", str(uuid.uuid4()), path)
        for method in sorted(set(operations) & http_methods):
            routes.append((method.upper(), concrete_path))
    return routes


def test_there_are_protected_routes_to_check():
    assert len(_protected_routes()) > 0


@pytest.mark.parametrize("method, path", _protected_routes())
def test_every_api_route_requires_authentication(method, path):
    response = client.request(method, path)
    assert response.status_code == 401, f"{method} {path} risponde {response.status_code}"


def test_health_stays_public():
    assert client.get("/health").status_code == 200