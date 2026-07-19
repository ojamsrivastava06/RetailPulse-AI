from __future__ import annotations

import base64
import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from api.core.config import get_settings

api_key_scheme = APIKeyHeader(name=get_settings().api_key_header_name, auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthPrincipal:
    subject: str
    auth_type: str
    scopes: tuple[str, ...] = ("read",)


def _b64url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


def _verify_hs256(token: str, secret: str) -> dict[str, Any]:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".")
        header = json.loads(_b64url_decode(header_b64))
        if header.get("alg") != "HS256":
            raise ValueError("Unsupported JWT algorithm.")
        signed = f"{header_b64}.{payload_b64}".encode("utf-8")
        expected = hmac.new(secret.encode("utf-8"), signed, hashlib.sha256).digest()
        supplied = _b64url_decode(signature_b64)
        if not hmac.compare_digest(expected, supplied):
            raise ValueError("Invalid JWT signature.")
        return json.loads(_b64url_decode(payload_b64))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT token.") from exc


def verify_api_key(api_key: str | None) -> AuthPrincipal | None:
    if not api_key:
        return None
    settings = get_settings()
    for expected in settings.api_keys:
        if hmac.compare_digest(api_key, expected):
            return AuthPrincipal(subject="api-key-client", auth_type="api_key")
    return None


def verify_bearer_token(credentials: HTTPAuthorizationCredentials | None) -> AuthPrincipal | None:
    if credentials is None:
        return None
    settings = get_settings()
    if not settings.jwt_secret_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT authentication is not configured. Use an API key or set RETAILPULSE_JWT_SECRET.",
        )
    payload = _verify_hs256(credentials.credentials, settings.jwt_secret_key)
    subject = str(payload.get("sub") or "jwt-client")
    scopes = tuple(str(payload.get("scope", "read")).split())
    return AuthPrincipal(subject=subject, auth_type="jwt", scopes=scopes)


def authenticate(api_key: str | None, credentials: HTTPAuthorizationCredentials | None) -> AuthPrincipal:
    principal = verify_api_key(api_key)
    if principal:
        return principal
    principal = verify_bearer_token(credentials)
    if principal:
        return principal
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing or invalid authentication credentials.",
        headers={"WWW-Authenticate": "ApiKey, Bearer"},
    )

