import structlog
from fastapi import Depends, HTTPException, status
import uuid
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models import CurrentUser
from app.config import get_settings
import jwt
from functools import lru_cache

ALGORITHMS_LIST=["ES256"]
SUPABASE_URL = get_settings().supabase_url
ISSUER = f"{SUPABASE_URL.rstrip('/')}/auth/v1"

supabase_jwks = SUPABASE_URL + "/auth/v1/.well-known/jwks.json"

logger=structlog.get_logger()
security = HTTPBearer(auto_error=False)

class AuthError(Exception):
    """Token is missing or not valid."""

@lru_cache(maxsize=1)
def get_jwks_client() -> jwt.PyJWKClient:
    return jwt.PyJWKClient(supabase_jwks, timeout=5)

def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate":"Bearer"}
    )

def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)) -> CurrentUser:
    if credentials is None:
        logger.warning("auth_failed", reason="missing_credentials")
        raise _unauthorized()
    try:
        user_id = verify_token(credentials.credentials)
    except AuthError as exc:
        logger.warning("auth_failed", reason=str(exc))
        raise _unauthorized()
    return CurrentUser(id=user_id)


def verify_token(token: str) -> uuid.UUID:
    try:
        jwks = get_jwks_client()
        signing_key=jwks.get_signing_key_from_jwt(token)
        claims = jwt.decode(token, signing_key.key, audience="authenticated", algorithms=ALGORITHMS_LIST, issuer=ISSUER, options={"require": ["exp", "sub"]})
        return uuid.UUID(str(claims["sub"]))
    except (jwt.PyJWTError, ValueError) as exc:
        raise AuthError(type(exc).__name__)