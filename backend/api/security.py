from datetime import datetime, timedelta, timezone
from typing import Any, Callable, cast

import jwt
from pwdlib import PasswordHash

from .database import Document
from .settings import ACCESS_TOKEN_MINUTES, JWT_ALGORITHM, JWT_SECRET

PASSWORD_HASHER = PasswordHash.recommended()


def create_access_token(user: Document) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, str | datetime] = {
        "sub": str(user["_id"]),
        "iat": now,
        "exp": now + timedelta(minutes=ACCESS_TOKEN_MINUTES),
    }
    encode = cast(Callable[..., str], jwt.encode)
    return encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def read_token_subject(token: str) -> str:
    decode = cast(Callable[..., dict[str, Any]], jwt.decode)
    payload = decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise jwt.InvalidTokenError("El token no contiene un sujeto válido.")
    return subject
