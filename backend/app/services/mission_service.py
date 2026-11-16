from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services import coop_service


ALLOWED_CONTEXT_TAGS = {
    "escola",
    "prova",
    "apresentacao",
    "familia",
    "amizade",
    "rotina",
    "sono",
    "estudos",
    "conflito",
    "social",
    "foco",
}


def _are_blocked(db: Session, user_a: int, user_b: int) -> bool:
    row = db.execute(
        text(
            """
            SELECT 1
            FROM blocks
            WHERE (blocker_user_pk = :a AND blocked_user_pk = :b)
               OR (blocker_user_pk = :b AND blocked_user_pk = :a)
            LIMIT 1
            """
        ),
        {"a": user_a, "b": user_b},
    ).first()
    return row is not None


def create_mission(
    db: Session,
    creator_user_pk: int,
    category: str,
    intensity: int,
    context_tags: list[str],
    want_now: str,
    partner_user_id: str | None = None,
) -> dict[str, Any]:
    if not set(context_tags).issubset(ALLOWED_CONTEXT_TAGS):
        raise ValueError("invalid context tags")

    if not partner_user_id:
        raise ValueError("partner_user_id is required")

    target_user_pk: int | None = None
    target_user_id: str | None = None
    if partner_user_id:
        partner = db.execute(
            text(
                """
                SELECT id, user_id, username
                FROM users
                WHERE user_id = :user_id AND role = 'user'
                """
            ),
            {"user_id": partner_user_id},
        ).mappings().first()
        if not partner:
            raise ValueError("partner user not found")
        target_user_pk = int(partner["id"])
        target_user_id = str(partner["user_id"])
        if target_user_pk == creator_user_pk:
            raise ValueError("cannot target yourself")
        if _are_blocked(db, creator_user_pk, target_user_pk):
            raise PermissionError("interaction blocked")
        if not coop_service.has_active_pair(db, creator_user_pk, target_user_pk):
            raise ValueError("active coop pair required for targeted mission")

    expires_at = datetime.now(UTC) + timedelta(hours=48)
    row = db.execute(
        text(
            """
            INSERT INTO missions (
                creator_user_pk, target_user_pk, category, intensity, context_tags_json, want_now,
                status, expires_at
            ) VALUES (
                :creator_user_pk, :target_user_pk, :category, :intensity, :context_tags_json, :want_now,
                'open', :expires_at
            )
            RETURNING id, status, expires_at, target_user_pk
            """
        ),
        {
            "creator_user_pk": creator_user_pk,
            "target_user_pk": target_user_pk,
            "category": category,
            "intensity": intensity,
            "context_tags_json": json.dumps(context_tags),
            "want_now": want_now,
            "expires_at": expires_at.isoformat(),
        },
    ).mappings().one()
    db.commit()
    return {
        "id": int(row["id"]),
        "status": row["status"],
        "expires_at": row["expires_at"],
        "target_user_id": target_user_id,
        "is_targeted": row["target_user_pk"] is not None,
    }


def feed(db: Session, user_pk: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
                m.id,
                m.category,
                m.intensity,
                m.context_tags_json,
                m.want_now,
                (SELECT COUNT(*) FROM mission_responses mr WHERE mr.mission_id = m.id) AS response_count,
                m.creator_user_pk,
                m.target_user_pk,
                u.user_id AS creator_user_id,
                u2.user_id AS target_user_id
            FROM missions m
            JOIN users u ON u.id = m.creator_user_pk
            LEFT JOIN users u2 ON u2.id = m.target_user_pk
            WHERE m.status = 'open'
              AND (m.expires_at IS NULL OR m.expires_at >= :now)
              AND m.target_user_pk IS NOT NULL
              AND (
                m.creator_user_pk = :user_pk
                OR m.target_user_pk = :user_pk
              )
            ORDER BY m.created_at DESC
            LIMIT 100
            """
        ),
        {"now": datetime.now(UTC).isoformat(), "user_pk": user_pk},
    ).mappings().all()

    result = []
    for row in rows:
        if _are_blocked(db, user_pk, int(row["creator_user_pk"])):
            continue
        item = dict(row)
        item["context_tags"] = json.loads(item.pop("context_tags_json"))
        item["is_targeted"] = item.get("target_user_pk") is not None
        item["is_mine"] = int(item["creator_user_pk"]) == user_pk
        result.append(item)
    return result


def inbox(db: Session, user_pk: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
              m.id,
              m.creator_user_pk,
              m.category,
              m.intensity,
              m.context_tags_json,
              m.want_now,
              m.expires_at,
              m.created_at,
              u.user_id AS creator_user_id,
              u.username AS creator_username
            FROM missions m
            JOIN users u ON u.id = m.creator_user_pk
            WHERE m.status = 'open'
              AND m.target_user_pk = :user_pk
              AND (m.expires_at IS NULL OR m.expires_at >= :now)
              AND NOT EXISTS (
                SELECT 1
                FROM mission_responses mr
                WHERE mr.mission_id = m.id AND mr.responder_user_pk = :user_pk
              )
            ORDER BY m.created_at DESC
            """
        ),
        {"user_pk": user_pk, "now": datetime.now(UTC).isoformat()},
    ).mappings().all()

    items: list[dict[str, Any]] = []
    for row in rows:
        if _are_blocked(db, user_pk, int(row["creator_user_pk"])):
            continue
        item = dict(row)
        item["context_tags"] = json.loads(item.pop("context_tags_json"))
        item["message"] = f"Você recebeu uma missão de ({item['creator_username']})."
        items.append(item)
    return items


def get_mission(db: Session, mission_id: int, viewer_user_pk: int) -> dict[str, Any] | None:
    row = db.execute(
        text(
            """
            SELECT
              m.id,
              m.creator_user_pk,
              m.target_user_pk,
              m.category,
              m.intensity,
              m.context_tags_json,
              m.want_now,
              m.status,
              m.expires_at,
              u.user_id AS creator_user_id,
              u.username AS creator_username,
              u2.user_id AS target_user_id
            FROM missions
            m
            JOIN users u ON u.id = m.creator_user_pk
            LEFT JOIN users u2 ON u2.id = m.target_user_pk
            WHERE m.id = :mission_id
            """
        ),
        {"mission_id": mission_id},
    ).mappings().first()
    if not row:
        return None
    if _are_blocked(db, viewer_user_pk, int(row["creator_user_pk"])):
        raise PermissionError("interaction blocked")
    target_user_pk = row["target_user_pk"]
    if target_user_pk is not None and viewer_user_pk not in {int(row["creator_user_pk"]), int(target_user_pk)}:
        raise PermissionError("mission reserved for coop partner")

    item = dict(row)
    item["context_tags"] = json.loads(item.pop("context_tags_json"))
    item["is_targeted"] = target_user_pk is not None
    item["is_mine"] = int(item["creator_user_pk"]) == viewer_user_pk
    item["response_count"] = int(
        db.execute(
            text("SELECT COUNT(*) FROM mission_responses WHERE mission_id = :mission_id"),
            {"mission_id": mission_id},
        ).scalar_one()
    )
    return item


def list_support_cards(db: Session, *, category: str, tone: str) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT id, card_key, category, tone, title, body, guided_actions_json
            FROM support_cards
            WHERE is_active = 1 AND category = :category AND tone = :tone
            ORDER BY id
            """
        ),
        {"category": category, "tone": tone},
    ).mappings().all()
    items = []
    for row in rows:
        item = dict(row)
        item["guided_actions"] = json.loads(item.pop("guided_actions_json"))
        items.append(item)
    return items


def respond(
    db: Session,
    *,
    mission_id: int,
    responder_user_pk: int,
    card_id: int,
    guided_actions_selected: list[str],
) -> dict[str, Any]:
    mission = db.execute(
        text(
            """
            SELECT id, creator_user_pk, target_user_pk, category, want_now, status, expires_at
            FROM missions
            WHERE id = :mission_id
            """
        ),
        {"mission_id": mission_id},
    ).mappings().first()
    if not mission:
        raise ValueError("mission not found")
    if mission["status"] != "open":
        raise ValueError("mission not open")
    if mission["creator_user_pk"] == responder_user_pk:
        raise ValueError("cannot respond own mission")
    target_user_pk = mission["target_user_pk"]
    if target_user_pk is not None and int(target_user_pk) != responder_user_pk:
        raise PermissionError("mission reserved for invited coop partner")
    if mission["expires_at"]:
        expires_at = datetime.fromisoformat(str(mission["expires_at"]).replace("Z", "+00:00"))
        if expires_at < datetime.now(UTC):
            raise ValueError("mission expired")
    if _are_blocked(db, responder_user_pk, int(mission["creator_user_pk"])):
        raise PermissionError("interaction blocked")
    if target_user_pk is not None and not coop_service.has_active_pair(db, int(mission["creator_user_pk"]), responder_user_pk):
        raise PermissionError("active coop pair required")

    card = db.execute(
        text(
            """
            SELECT id, category, tone
            FROM support_cards
            WHERE id = :card_id AND is_active = 1
            """
        ),
        {"card_id": card_id},
    ).mappings().first()
    if not card:
        raise ValueError("card not found")
    if card["category"] != mission["category"]:
        raise ValueError("card category mismatch")
    if card["tone"] != mission["want_now"]:
        raise ValueError("card tone mismatch")

    row = db.execute(
        text(
            """
            INSERT INTO mission_responses (mission_id, responder_user_pk, card_id, guided_actions_selected_json, status)
            VALUES (:mission_id, :responder_user_pk, :card_id, :guided_actions_selected_json, 'active')
            RETURNING id, status
            """
        ),
        {
            "mission_id": mission_id,
            "responder_user_pk": responder_user_pk,
            "card_id": card_id,
            "guided_actions_selected_json": json.dumps(guided_actions_selected),
        },
    ).mappings().one()
    db.commit()
    return {"response_id": int(row["id"]), "status": row["status"]}


def feedback(
    db: Session,
    *,
    mission_id: int,
    from_user_pk: int,
    response_id: int,
    useful: bool,
    best_response: bool,
) -> dict[str, Any]:
    mission = db.execute(
        text("SELECT id, creator_user_pk FROM missions WHERE id = :mission_id"),
        {"mission_id": mission_id},
    ).mappings().first()
    if not mission:
        raise ValueError("mission not found")
    if int(mission["creator_user_pk"]) != from_user_pk:
        raise PermissionError("only creator can rate")

    response = db.execute(
        text("SELECT id, responder_user_pk FROM mission_responses WHERE id = :response_id AND mission_id = :mission_id"),
        {"response_id": response_id, "mission_id": mission_id},
    ).mappings().first()
    if not response:
        raise ValueError("response not found")

    db.execute(
        text(
            """
            INSERT INTO mission_feedback (mission_id, response_id, from_user_pk, is_useful, is_best_response)
            VALUES (:mission_id, :response_id, :from_user_pk, :is_useful, :is_best_response)
            """
        ),
        {
            "mission_id": mission_id,
            "response_id": response_id,
            "from_user_pk": from_user_pk,
            "is_useful": 1 if useful else 0,
            "is_best_response": 1 if best_response else 0,
        },
    )

    xp = 0
    if useful:
        xp += 10
    if best_response:
        xp += 5
        db.execute(
            text("UPDATE missions SET status='resolved' WHERE id = :mission_id"),
            {"mission_id": mission_id},
        )

    coop_bonus_applied = False
    if xp > 0 and coop_service.has_active_pair(db, int(mission["creator_user_pk"]), int(response["responder_user_pk"])):
        xp *= 2
        coop_bonus_applied = True

    if xp > 0:
        db.execute(
            text(
                """
                INSERT INTO xp_events (user_pk, source_type, source_id, points, reason)
                VALUES (:user_pk, 'mission_response_useful', :source_id, :points, :reason)
                """
            ),
            {
                "user_pk": response["responder_user_pk"],
                "source_id": str(response_id),
                "points": xp,
                "reason": "mission feedback with coop bonus" if coop_bonus_applied else "mission feedback",
            },
        )
    db.commit()

    return {
        "message": "Feedback registrado",
        "xp_awarded_to_responder": xp,
        "coop_bonus_applied": coop_bonus_applied,
    }
