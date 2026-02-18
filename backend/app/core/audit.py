import json
from typing import Any

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.orm import Session


def write_audit(
    db: Session,
    *,
    actor_user_pk: int | None,
    actor_role: str,
    action: str,
    entity_type: str,
    entity_id: str | None,
    payload: dict[str, Any] | None,
    request: Request | None,
) -> int:
    ip_address = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None

    row = db.execute(
        text(
            """
            INSERT INTO audit_log (
                actor_user_pk, actor_role, action, entity_type, entity_id,
                payload_json, ip_address, user_agent
            ) VALUES (
                :actor_user_pk, :actor_role, :action, :entity_type, :entity_id,
                :payload_json, :ip_address, :user_agent
            )
            RETURNING id
            """
        ),
        {
            "actor_user_pk": actor_user_pk,
            "actor_role": actor_role,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "payload_json": json.dumps(payload or {}),
            "ip_address": ip_address,
            "user_agent": user_agent,
        },
    ).scalar_one()
    db.commit()
    return int(row)
