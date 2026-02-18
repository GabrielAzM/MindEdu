from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import generate_recovery_token, hash_password, hash_token


OUTBOX_PATH = Path("data/recovery_outbox.log")


def _write_outbox(email: str, request_id: str, token: str, request_type: str) -> None:
    OUTBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "email": email,
        "request_id": request_id,
        "token": token,
        "request_type": request_type,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    with OUTBOX_PATH.open("a", encoding="utf-8") as fp:
        fp.write(json.dumps(payload) + "\n")


def create_recovery_request(db: Session, email: str, request_type: str, requested_by_admin_pk: int | None = None) -> str:
    settings = get_settings()
    request_id = f"req_{uuid4().hex[:12]}"
    token = generate_recovery_token()
    expires_at = datetime.now(UTC) + timedelta(minutes=settings.recovery_token_minutes)

    user_row = db.execute(
        text("SELECT id FROM users WHERE email = :email"),
        {"email": email.lower()},
    ).mappings().first()

    db.execute(
        text(
            """
            INSERT INTO account_requests (
                request_id, user_pk, email, request_type, token_hash,
                expires_at, requested_by_admin_pk
            ) VALUES (
                :request_id, :user_pk, :email, :request_type, :token_hash,
                :expires_at, :requested_by_admin_pk
            )
            """
        ),
        {
            "request_id": request_id,
            "user_pk": user_row["id"] if user_row else None,
            "email": email.lower(),
            "request_type": request_type,
            "token_hash": hash_token(token),
            "expires_at": expires_at.isoformat(),
            "requested_by_admin_pk": requested_by_admin_pk,
        },
    )
    db.commit()

    _write_outbox(email.lower(), request_id, token, request_type)
    return request_id


def confirm_recovery(db: Session, request_id: str, token: str, new_password: str | None) -> dict:
    row = db.execute(
        text(
            """
            SELECT id, user_pk, request_type, token_hash, expires_at, status
            FROM account_requests
            WHERE request_id = :request_id
            """
        ),
        {"request_id": request_id},
    ).mappings().first()
    if not row:
        raise ValueError("request not found")
    if row["status"] != "pending":
        raise ValueError("request not pending")

    expires_at = datetime.fromisoformat(str(row["expires_at"]).replace("Z", "+00:00"))
    if expires_at < datetime.now(UTC):
        db.execute(
            text("UPDATE account_requests SET status='expired' WHERE id = :id"),
            {"id": row["id"]},
        )
        db.commit()
        raise ValueError("request expired")

    if hash_token(token) != row["token_hash"]:
        raise ValueError("invalid token")

    if row["request_type"] == "forgot_id":
        user = db.execute(
            text("SELECT user_id FROM users WHERE id = :id"),
            {"id": row["user_pk"]},
        ).mappings().first()
        if not user:
            raise ValueError("user not found")

        db.execute(
            text(
                """
                UPDATE account_requests
                SET status='confirmed', confirmed_at=:confirmed_at
                WHERE id = :id
                """
            ),
            {"id": row["id"], "confirmed_at": datetime.now(UTC).isoformat()},
        )
        db.commit()
        return {"user_id": user["user_id"]}

    if row["request_type"] == "reset_password":
        if not new_password:
            raise ValueError("new_password required")
        db.execute(
            text("UPDATE users SET password_hash = :password_hash WHERE id = :id"),
            {"password_hash": hash_password(new_password), "id": row["user_pk"]},
        )
        db.execute(
            text(
                """
                UPDATE account_requests
                SET status='confirmed', confirmed_at=:confirmed_at
                WHERE id = :id
                """
            ),
            {"id": row["id"], "confirmed_at": datetime.now(UTC).isoformat()},
        )
        db.commit()
        return {"message": "Senha redefinida com sucesso."}

    raise ValueError("unsupported request type")

