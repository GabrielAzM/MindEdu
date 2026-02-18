from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.jwt import create_access_token, create_refresh_token, decode_token
from app.core.security import generate_user_id, hash_password, hash_token, verify_password


def _get_user_by_user_id(db: Session, user_id: str) -> dict | None:
    row = db.execute(
        text(
            """
            SELECT id, user_id, email, username, password_hash, role, status, muted_until, approval_status
            FROM users
            WHERE user_id = :user_id
            """
        ),
        {"user_id": user_id},
    ).mappings().first()
    return dict(row) if row else None


def _get_user_by_email(db: Session, email: str) -> dict | None:
    row = db.execute(
        text(
            """
            SELECT id, user_id, email, username, password_hash, role, status, muted_until, approval_status
            FROM users
            WHERE email = :email
            """
        ),
        {"email": email.lower()},
    ).mappings().first()
    return dict(row) if row else None


def register_user(db: Session, email: str, username: str, password: str) -> dict:
    if _get_user_by_email(db, email):
        raise ValueError("email already registered")

    user_id = generate_user_id()
    while _get_user_by_user_id(db, user_id):
        user_id = generate_user_id()

    password_hash = hash_password(password)
    row = db.execute(
        text(
            """
            INSERT INTO users (user_id, email, username, password_hash, role, status, approval_status)
            VALUES (:user_id, :email, :username, :password_hash, 'user', 'active', 'pending')
            RETURNING id, user_id, username, role, status
            """
        ),
        {
            "user_id": user_id,
            "email": email.lower(),
            "username": username,
            "password_hash": password_hash,
        },
    ).mappings().one()
    db.commit()
    return dict(row)


def authenticate(db: Session, user_id: str, password: str) -> dict:
    user = _get_user_by_user_id(db, user_id)
    if not user or not verify_password(password, user["password_hash"]):
        raise ValueError("invalid credentials")
    if user["role"] == "user":
        approval_status = user.get("approval_status")
        if approval_status == "rejected":
            raise PermissionError("account rejected by admin")
        if approval_status != "approved":
            raise PermissionError("account pending admin approval")
    if user["status"] == "banned":
        raise PermissionError("user banned")
    return user


def issue_tokens(db: Session, user: dict) -> dict:
    access_token, access_exp = create_access_token(user["user_id"], user["role"], user["status"])
    refresh_token, refresh_exp = create_refresh_token(user["user_id"])

    db.execute(
        text(
            """
            INSERT INTO refresh_tokens (user_pk, token_hash, expires_at)
            VALUES (:user_pk, :token_hash, :expires_at)
            """
        ),
        {
            "user_pk": user["id"],
            "token_hash": hash_token(refresh_token),
            "expires_at": refresh_exp.isoformat(),
        },
    )
    db.execute(
        text("UPDATE users SET last_login_at = :now WHERE id = :user_pk"),
        {"now": datetime.now(UTC).isoformat(), "user_pk": user["id"]},
    )
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": int((access_exp - datetime.now(UTC)).total_seconds()),
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "status": user["status"],
        },
    }


def refresh(db: Session, refresh_token: str) -> dict:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise ValueError("invalid refresh token")

    token_hash_value = hash_token(refresh_token)
    token_row = db.execute(
        text(
            """
            SELECT id, user_pk, expires_at, revoked_at
            FROM refresh_tokens
            WHERE token_hash = :token_hash
            """
        ),
        {"token_hash": token_hash_value},
    ).mappings().first()
    if not token_row:
        raise ValueError("refresh token not found")
    if token_row["revoked_at"] is not None:
        raise ValueError("refresh token revoked")

    expires_at = datetime.fromisoformat(str(token_row["expires_at"]).replace("Z", "+00:00"))
    if expires_at < datetime.now(UTC):
        raise ValueError("refresh token expired")

    user = db.execute(
        text("SELECT id, user_id, username, role, status FROM users WHERE id = :id"),
        {"id": token_row["user_pk"]},
    ).mappings().first()
    if not user:
        raise ValueError("user not found")

    db.execute(
        text("UPDATE refresh_tokens SET revoked_at = :revoked_at WHERE id = :id"),
        {"revoked_at": datetime.now(UTC).isoformat(), "id": token_row["id"]},
    )
    db.commit()

    return issue_tokens(db, dict(user))


def get_user_by_id(db: Session, user_pk: int) -> dict | None:
    row = db.execute(
        text("SELECT id, user_id, username, role, status, approval_status FROM users WHERE id = :id"),
        {"id": user_pk},
    ).mappings().first()
    return dict(row) if row else None


def ensure_default_admin(db: Session) -> None:
    existing = db.execute(text("SELECT id FROM users WHERE role = 'admin' LIMIT 1")).mappings().first()
    if existing:
        db.execute(
            text(
                """
                UPDATE users
                SET approval_status = 'approved',
                    approved_at = COALESCE(approved_at, :approved_at),
                    rejected_reason = NULL
                WHERE id = :id
                """
            ),
            {"id": existing["id"], "approved_at": datetime.now(UTC).isoformat()},
        )
        db.commit()
        return

    db.execute(
        text(
            """
            INSERT INTO users (user_id, email, username, password_hash, role, status, approval_status, approved_at)
            VALUES (:user_id, :email, :username, :password_hash, 'admin', 'active', 'approved', :approved_at)
            """
        ),
        {
            "user_id": "MDU-ADMIN-0001",
            "email": "admin@mindedu.local",
            "username": "Admin",
            "password_hash": hash_password("Admin12345"),
            "approved_at": datetime.now(UTC).isoformat(),
        },
    )
    db.commit()
