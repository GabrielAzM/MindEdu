from __future__ import annotations

import json
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jsonschema import ValidationError, validate
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.jwt import decode_token
from app.core.rate_limit import rate_limiter
from app.db.session import get_db
from app.schemas.contracts import UserCtx

security = HTTPBearer(auto_error=True)

SCHEMA_MAP = {
    "auth": "auth.schema.json",
    "recovery": "recovery.schema.json",
    "content": "content.schema.json",
    "emotions": "emotions.schema.json",
    "uxu": "uxu.schema.json",
    "moderation": "moderation.schema.json",
    "admin": "admin.schema.json",
    "reports": "reports.schema.json",
}


@lru_cache(maxsize=32)
def _load_schema(name: str) -> dict[str, Any]:
    filename = SCHEMA_MAP[name]
    root = Path("shared/generated") / filename
    if not root.exists():
        root = Path(__file__).resolve().parents[3] / "shared" / "generated" / filename
    return json.loads(root.read_text(encoding="utf-8"))


def validate_payload(schema_name: str, definition_name: str, payload: dict[str, Any]) -> None:
    schema = _load_schema(schema_name)
    definition = schema.get("definitions", {}).get(definition_name)
    if not definition:
        raise RuntimeError(f"schema definition not found: {schema_name}.{definition_name}")
    try:
        validate(payload, definition)
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=exc.message) from exc


def get_request_ip(request: Request) -> str | None:
    if request.client:
        return request.client.host
    return None


def enforce_rate_limit(
    db: Session,
    *,
    action_key: str,
    max_hits: int,
    window_seconds: int,
    user_pk: int | None,
    ip_address: str | None,
) -> None:
    allowed = rate_limiter.check_and_record(
        db,
        action_key=action_key,
        max_hits=max_hits,
        window_seconds=window_seconds,
        user_pk=user_pk,
        ip_address=ip_address,
    )
    if not allowed:
        raise HTTPException(status_code=429, detail="rate limit exceeded")


def _fetch_user_by_user_id(db: Session, user_id: str) -> UserCtx:
    row = db.execute(
        text(
            """
            SELECT id, user_id, username, role, status, muted_until, approval_status
            FROM users
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=401, detail="invalid credentials")

    status_value = row["status"]
    muted_until = row["muted_until"]
    if status_value == "muted" and muted_until:
        try:
            until = datetime.fromisoformat(str(muted_until).replace("Z", "+00:00"))
            if until < datetime.now(UTC):
                db.execute(text("UPDATE users SET status='active', muted_until=NULL WHERE id=:id"), {"id": row["id"]})
                db.commit()
                status_value = "active"
        except ValueError:
            pass

    if str(row["role"]) == "user" and str(row.get("approval_status") or "pending") != "approved":
        raise HTTPException(status_code=403, detail="account pending admin approval")

    return UserCtx(
        pk=int(row["id"]),
        user_id=str(row["user_id"]),
        username=str(row["username"]),
        role=str(row["role"]),
        status=status_value,
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> UserCtx:
    token = credentials.credentials
    try:
        payload = decode_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail="invalid token") from exc

    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="invalid token type")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="invalid token subject")

    return _fetch_user_by_user_id(db, user_id)


def require_admin(user: UserCtx = Depends(get_current_user)) -> UserCtx:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="admin only")
    return user


def require_not_muted(user: UserCtx = Depends(get_current_user)) -> UserCtx:
    if user.status == "muted":
        raise HTTPException(status_code=403, detail="user muted")
    if user.status == "banned":
        raise HTTPException(status_code=403, detail="user banned")
    return user
