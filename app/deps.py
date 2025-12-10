from fastapi import Depends, Request, HTTPException, status
from sqlalchemy.orm import Session
from time import time

from app.database import SessionLocal




_RATE_LIMIT_STORE: dict[str, list[float]] = {}
MAX_REQUESTS_PER_MINUTE = 5
WINDOW_SECONDS = 60


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def rate_limit_dep(request: Request):
    client_ip = request.client.host if request.client else "unknown"
    now = time()

    timestamps = _RATE_LIMIT_STORE.get(client_ip, [])
    
    timestamps = [ts for ts in timestamps if now - ts < WINDOW_SECONDS]

    if len(timestamps) >= MAX_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests, please slow down",
        )

    timestamps.append(now)
    _RATE_LIMIT_STORE[client_ip] = timestamps
    return
