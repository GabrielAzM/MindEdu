from __future__ import annotations

import json
import secrets
import string
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.security import generate_user_id, hash_password


def create_report(
    db: Session,
    *,
    reporter_user_pk: int,
    target_type: str,
    target_id: str,
    reason: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            INSERT INTO reports (reporter_user_pk, target_type, target_id, reason, details_json, status)
            VALUES (:reporter_user_pk, :target_type, :target_id, :reason, :details_json, 'open')
            RETURNING id, status
            """
        ),
        {
            "reporter_user_pk": reporter_user_pk,
            "target_type": target_type,
            "target_id": target_id,
            "reason": reason,
            "details_json": json.dumps(details),
        },
    ).mappings().one()
    db.commit()
    return {"report_id": int(row["id"]), "status": row["status"]}


def block_user(db: Session, blocker_user_pk: int, blocked_user_id: str) -> dict[str, Any]:
    target = db.execute(
        text("SELECT id FROM users WHERE user_id = :user_id"),
        {"user_id": blocked_user_id},
    ).mappings().first()
    if not target:
        raise ValueError("target user not found")
    if int(target["id"]) == blocker_user_pk:
        raise ValueError("cannot block self")

    db.execute(
        text(
            """
            INSERT OR IGNORE INTO blocks (blocker_user_pk, blocked_user_pk)
            VALUES (:blocker_user_pk, :blocked_user_pk)
            """
        ),
        {
            "blocker_user_pk": blocker_user_pk,
            "blocked_user_pk": target["id"],
        },
    )
    db.commit()
    return {"message": "Usuario bloqueado com sucesso."}


def list_reports(db: Session, status: str | None = None) -> list[dict[str, Any]]:
    query = "SELECT id, target_type, target_id, reason, status, created_at FROM reports"
    params: dict[str, Any] = {}
    if status:
        query += " WHERE status = :status"
        params["status"] = status
    query += " ORDER BY created_at DESC"
    rows = db.execute(text(query), params).mappings().all()
    return [dict(r) for r in rows]


def resolve_report(db: Session, report_id: int, admin_user_pk: int, resolution: str, note: str) -> dict[str, Any]:
    report = db.execute(
        text("SELECT id FROM reports WHERE id = :id"),
        {"id": report_id},
    ).mappings().first()
    if not report:
        raise ValueError("report not found")

    status = "resolved" if resolution == "action_taken" else "dismissed"
    db.execute(
        text(
            """
            UPDATE reports
            SET status = :status,
                resolved_by_user_pk = :admin_user_pk,
                resolution_note = :note,
                resolved_at = :resolved_at
            WHERE id = :id
            """
        ),
        {
            "id": report_id,
            "status": status,
            "admin_user_pk": admin_user_pk,
            "note": note,
            "resolved_at": datetime.now(UTC).isoformat(),
        },
    )
    db.commit()
    return {"status": status}


def _new_temp_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "TMP" + "".join(secrets.choice(alphabet) for _ in range(9))


def admin_user_action(
    db: Session,
    *,
    admin_user_pk: int,
    target_user_id: str,
    action: str,
    reason: str,
    duration_minutes: int | None,
) -> dict[str, Any]:
    user = db.execute(
        text("SELECT id, user_id, status FROM users WHERE user_id = :user_id"),
        {"user_id": target_user_id},
    ).mappings().first()
    if not user:
        raise ValueError("target user not found")

    metadata: dict[str, Any] = {}

    if action == "warn":
        pass
    elif action == "mute":
        minutes = duration_minutes or 60
        muted_until = datetime.now(UTC) + timedelta(minutes=minutes)
        db.execute(
            text("UPDATE users SET status='muted', muted_until=:muted_until WHERE id=:id"),
            {"id": user["id"], "muted_until": muted_until.isoformat()},
        )
        metadata["muted_until"] = muted_until.isoformat()
    elif action == "ban":
        db.execute(text("UPDATE users SET status='banned', muted_until=NULL WHERE id=:id"), {"id": user["id"]})
    elif action == "unban":
        db.execute(text("UPDATE users SET status='active', muted_until=NULL WHERE id=:id"), {"id": user["id"]})
    elif action == "reset_password":
        temp_password = _new_temp_password()
        db.execute(
            text("UPDATE users SET password_hash=:password_hash WHERE id=:id"),
            {"id": user["id"], "password_hash": hash_password(temp_password)},
        )
        metadata["temporary_password"] = temp_password
    elif action == "reset_user_id":
        new_user_id = generate_user_id()
        exists = db.execute(text("SELECT id FROM users WHERE user_id=:u"), {"u": new_user_id}).first()
        while exists:
            new_user_id = generate_user_id()
            exists = db.execute(text("SELECT id FROM users WHERE user_id=:u"), {"u": new_user_id}).first()
        db.execute(text("UPDATE users SET user_id=:new_user_id WHERE id=:id"), {"id": user["id"], "new_user_id": new_user_id})
        metadata["new_user_id"] = new_user_id
    else:
        raise ValueError("unsupported action")

    action_row = db.execute(
        text(
            """
            INSERT INTO moderation_actions (admin_user_pk, target_user_pk, action, reason, duration_minutes, metadata_json)
            VALUES (:admin_user_pk, :target_user_pk, :action, :reason, :duration_minutes, :metadata_json)
            RETURNING id
            """
        ),
        {
            "admin_user_pk": admin_user_pk,
            "target_user_pk": user["id"],
            "action": action,
            "reason": reason,
            "duration_minutes": duration_minutes,
            "metadata_json": json.dumps(metadata),
        },
    ).mappings().one()
    db.commit()

    payload = {
        "status": "ok",
        "action_id": int(action_row["id"]),
    }
    payload.update(metadata)
    return payload


def admin_delete_user(
    db: Session,
    *,
    admin_user_pk: int,
    target_user_id: str,
    reason: str,
) -> dict[str, Any]:
    user = db.execute(
        text("SELECT id, user_id, role FROM users WHERE user_id = :user_id"),
        {"user_id": target_user_id},
    ).mappings().first()
    if not user:
        raise ValueError("target user not found")
    if str(user["role"]) != "user":
        raise ValueError("only regular users can be deleted")

    if int(user["id"]) == admin_user_pk:
        raise ValueError("admin cannot delete own account")

    db.execute(
        text("DELETE FROM users WHERE id = :id"),
        {"id": int(user["id"])},
    )
    db.commit()
    return {
        "deleted_user_id": str(user["user_id"]),
        "reason": reason,
    }
