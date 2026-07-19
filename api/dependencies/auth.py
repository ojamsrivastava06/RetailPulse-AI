from __future__ import annotations

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials

from api.core.security import AuthPrincipal, api_key_scheme, authenticate, bearer_scheme


def get_current_principal(
    api_key: str | None = Depends(api_key_scheme),
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthPrincipal:
    return authenticate(api_key, credentials)

