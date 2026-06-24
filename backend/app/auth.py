from hmac import compare_digest
import logging

from fastapi import HTTPException, Security, status, Request
from fastapi.security import APIKeyHeader

from app.config import settings

logger = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _mask_key(key: str | None) -> str:
    if not key:
        return "<missing>"
    if len(key) <= 6:
        return key
    return f"{key[:3]}...{key[-3:]}"


def require_api_key(api_key: str | None = Security(api_key_header)) -> None:
    """Dependency that enforces presence of a valid API key.

    Adds masked logging to help diagnose missing/incorrect API keys during
    development. Avoids logging full secrets.
    """
    # Basic configuration verification
    if not settings.API_AUTH_TOKEN:
        logger.error("API_AUTH_TOKEN is not configured in settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API authentication is not configured.",
        )

    # Log presence and masked values for debugging (do not log full tokens)
    provided_masked = _mask_key(api_key)
    expected_masked = _mask_key(settings.API_AUTH_TOKEN)
    logger.debug("API auth check: provided=%s expected=%s", provided_masked, expected_masked)

    if not api_key or not compare_digest(api_key, settings.API_AUTH_TOKEN):
        logger.warning("API auth failed: provided=%s expected=%s", provided_masked, expected_masked)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key.",
        )
