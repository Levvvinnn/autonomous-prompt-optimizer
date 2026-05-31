from collections import defaultdict, deque
from threading import Lock
from time import monotonic

from fastapi import HTTPException, Request, status

from app.config import settings

request_log: dict[str, deque[float]] = defaultdict(deque)
request_log_lock = Lock()


def get_client_key(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"api-key:{api_key}"

    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return f"ip:{forwarded_for.split(',')[0].strip()}"

    host = request.client.host if request.client else "unknown"
    return f"ip:{host}"


def rate_limit(request: Request) -> None:
    limit = settings.RATE_LIMIT_REQUESTS
    window = settings.RATE_LIMIT_WINDOW_SECONDS

    if limit <= 0 or window <= 0:
        return

    now = monotonic()
    cutoff = now - window
    client_key = get_client_key(request)

    with request_log_lock:
        timestamps = request_log[client_key]

        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()

        if len(timestamps)>=limit:
            retry_after = max(1, int(window - (now - timestamps[0])))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After":str(retry_after)},
            )

        timestamps.append(now)
