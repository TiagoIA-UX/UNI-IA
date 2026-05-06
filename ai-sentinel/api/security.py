import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader


ADMIN_TOKEN_HEADER = APIKeyHeader(name="X-UNI-IA-ADMIN-TOKEN", auto_error=False)


def require_admin_token(api_key: str = Security(ADMIN_TOKEN_HEADER)):
    expected_token = os.getenv("UNI_IA_ADMIN_TOKEN", "").strip()
    provided_token = (api_key or "").strip()

    if not expected_token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="admin_token_not_configured",
        )

    if not provided_token or not secrets.compare_digest(provided_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="unauthorized",
        )
