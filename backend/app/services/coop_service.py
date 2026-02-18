from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

FRIENDSHIP_XP_MILESTONES = [1, 10, 30, 50, 100, 200, 300, 500, 700, 1000]


def list_coop_challenges(db: Session) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT id, slug, title, category, description, steps_json, max_members, status
            FROM coop_challenges
            WHERE status = 'active'
            ORDER BY created_at DESC
            """
        )
    ).mappings().all()

    items = []
    for row in rows:
        item = dict(row)
        item["steps"] = json.loads(item.pop("steps_json"))
        items.append(item)
    return items


def _pair_key(user_a_pk: int, user_b_pk: int) -> tuple[int, int]:
    return (min(user_a_pk, user_b_pk), max(user_a_pk, user_b_pk))


def _active_friend_count(db: Session, user_pk: int) -> int:
    return int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM coop_pairs
                WHERE status = 'active'
                  AND (user_low_pk = :user_pk OR user_high_pk = :user_pk)
                """
            ),
            {"user_pk": user_pk},
        ).scalar_one()
    )


def _award_friendship_milestones(db: Session, user_pk: int) -> dict[str, Any]:
    active_friends = _active_friend_count(db, user_pk)
    already_awarded = {
        int(row["milestone"])
        for row in db.execute(
            text("SELECT milestone FROM friendship_xp_rewards WHERE user_pk = :user_pk"),
            {"user_pk": user_pk},
        ).mappings().all()
    }

    awarded_now: list[dict[str, int]] = []
    for milestone in FRIENDSHIP_XP_MILESTONES:
        if active_friends < milestone or milestone in already_awarded:
            continue
        xp_awarded = milestone
        db.execute(
            text(
                """
                INSERT INTO friendship_xp_rewards (user_pk, milestone, xp_awarded)
                VALUES (:user_pk, :milestone, :xp_awarded)
                """
            ),
            {
                "user_pk": user_pk,
                "milestone": milestone,
                "xp_awarded": xp_awarded,
            },
        )
        db.execute(
            text(
                """
                INSERT INTO xp_events (user_pk, source_type, source_id, points, reason)
                VALUES (:user_pk, 'coop', :source_id, :points, :reason)
                """
            ),
            {
                "user_pk": user_pk,
                "source_id": f"friendship:{milestone}",
                "points": xp_awarded,
                "reason": f"friendship milestone {milestone}",
            },
        )
        awarded_now.append({"milestone": milestone, "xp_awarded": xp_awarded})
    return {
        "active_friends": active_friends,
        "awarded_now": awarded_now,
        "xp_awarded_total": int(sum(item["xp_awarded"] for item in awarded_now)),
    }


def has_active_pair(db: Session, user_a_pk: int, user_b_pk: int) -> bool:
    low, high = _pair_key(user_a_pk, user_b_pk)
    row = db.execute(
        text(
            """
            SELECT 1
            FROM coop_pairs
            WHERE user_low_pk = :low
              AND user_high_pk = :high
              AND status = 'active'
            LIMIT 1
            """
        ),
        {"low": low, "high": high},
    ).first()
    return row is not None


def create_pair_request(db: Session, requester_user_pk: int, partner_user_id: str) -> dict[str, Any]:
    partner = db.execute(
        text("SELECT id, user_id, username FROM users WHERE user_id = :user_id AND role = 'user'"),
        {"user_id": partner_user_id},
    ).mappings().first()
    if not partner:
        raise ValueError("partner user not found")
    if int(partner["id"]) == requester_user_pk:
        raise ValueError("cannot create coop with yourself")

    low, high = _pair_key(requester_user_pk, int(partner["id"]))
    row = db.execute(
        text(
            """
            SELECT id, status, requested_by_user_pk
            FROM coop_pairs
            WHERE user_low_pk = :low AND user_high_pk = :high
            """
        ),
        {"low": low, "high": high},
    ).mappings().first()

    now = datetime.now(UTC).isoformat()
    if row:
        if row["status"] == "active":
            return {"pair_id": int(row["id"]), "status": "active", "partner_user_id": str(partner["user_id"])}
        if row["status"] == "pending":
            return {"pair_id": int(row["id"]), "status": "pending", "partner_user_id": str(partner["user_id"])}
        db.execute(
            text(
                """
                UPDATE coop_pairs
                SET status = 'pending',
                    requested_by_user_pk = :requested_by_user_pk,
                    created_at = :created_at,
                    confirmed_at = NULL,
                    rejected_at = NULL
                WHERE id = :id
                """
            ),
            {
                "id": row["id"],
                "requested_by_user_pk": requester_user_pk,
                "created_at": now,
            },
        )
        db.commit()
        return {"pair_id": int(row["id"]), "status": "pending", "partner_user_id": str(partner["user_id"])}

    created = db.execute(
        text(
            """
            INSERT INTO coop_pairs (user_low_pk, user_high_pk, requested_by_user_pk, status, created_at)
            VALUES (:low, :high, :requested_by_user_pk, 'pending', :created_at)
            RETURNING id
            """
        ),
        {
            "low": low,
            "high": high,
            "requested_by_user_pk": requester_user_pk,
            "created_at": now,
        },
    ).mappings().one()
    db.commit()
    return {"pair_id": int(created["id"]), "status": "pending", "partner_user_id": str(partner["user_id"])}


def list_pairs(db: Session, user_pk: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
              cp.id,
              cp.user_low_pk,
              cp.user_high_pk,
              cp.requested_by_user_pk,
              cp.status,
              cp.created_at,
              cp.confirmed_at,
              ul.user_id AS user_low_id,
              uh.user_id AS user_high_id,
              ul.username AS user_low_name,
              uh.username AS user_high_name
            FROM coop_pairs cp
            JOIN users ul ON ul.id = cp.user_low_pk
            JOIN users uh ON uh.id = cp.user_high_pk
            WHERE cp.user_low_pk = :user_pk OR cp.user_high_pk = :user_pk
            ORDER BY cp.created_at DESC
            """
        ),
        {"user_pk": user_pk},
    ).mappings().all()

    items: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        is_low = int(item["user_low_pk"]) == user_pk
        partner_user_pk = int(item["user_high_pk"]) if is_low else int(item["user_low_pk"])
        partner_user_id = str(item["user_high_id"]) if is_low else str(item["user_low_id"])
        partner_name = str(item["user_high_name"]) if is_low else str(item["user_low_name"])
        can_confirm = item["status"] == "pending" and int(item["requested_by_user_pk"]) != user_pk
        items.append(
            {
                "id": int(item["id"]),
                "status": item["status"],
                "created_at": item["created_at"],
                "confirmed_at": item["confirmed_at"],
                "partner_user_pk": partner_user_pk,
                "partner_user_id": partner_user_id,
                "partner_name": partner_name,
                "can_confirm": can_confirm,
            }
        )
    return items


def confirm_pair(db: Session, pair_id: int, actor_user_pk: int, accept: bool) -> dict[str, Any]:
    row = db.execute(
        text(
            """
            SELECT id, user_low_pk, user_high_pk, requested_by_user_pk, status
            FROM coop_pairs
            WHERE id = :id
            """
        ),
        {"id": pair_id},
    ).mappings().first()
    if not row:
        raise ValueError("pair request not found")

    low = int(row["user_low_pk"])
    high = int(row["user_high_pk"])
    if actor_user_pk not in {low, high}:
        raise PermissionError("not part of this pair request")
    if row["status"] != "pending":
        raise ValueError("pair request is not pending")
    if int(row["requested_by_user_pk"]) == actor_user_pk:
        raise PermissionError("requester cannot self-confirm")

    if not accept:
        db.execute(
            text(
                """
                UPDATE coop_pairs
                SET status = 'rejected', rejected_at = :rejected_at
                WHERE id = :id
                """
            ),
            {
                "id": pair_id,
                "rejected_at": datetime.now(UTC).isoformat(),
            },
        )
        db.commit()
        return {"status": "rejected"}

    now = datetime.now(UTC).isoformat()
    db.execute(
        text(
            """
            UPDATE coop_pairs
            SET status = 'active', confirmed_at = :confirmed_at
            WHERE id = :id
            """
        ),
        {
            "id": pair_id,
            "confirmed_at": now,
        },
    )

    requester_rewards = _award_friendship_milestones(db, low)
    partner_rewards = _award_friendship_milestones(db, high)
    db.commit()
    return {
        "status": "active",
        "friendship_xp": {
            "user_low_pk": requester_rewards,
            "user_high_pk": partner_rewards,
        },
    }
