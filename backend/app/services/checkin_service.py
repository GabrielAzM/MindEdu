from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def create_checkin(
    db: Session,
    user_pk: int,
    emotion: str,
    intensity: int,
    context_tags: list[str],
    need_tags: list[str],
) -> dict[str, Any]:
    today_utc = datetime.now(UTC).date().isoformat()
    daily_checkin_count = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM emotion_checkins
                WHERE user_pk = :user_pk
                  AND DATE(created_at) = :today_utc
                """
            ),
            {"user_pk": user_pk, "today_utc": today_utc},
        ).scalar_one()
    )

    row = db.execute(
        text(
            """
            INSERT INTO emotion_checkins (user_pk, emotion, intensity, context_tags_json, need_tags_json)
            VALUES (:user_pk, :emotion, :intensity, :context_tags_json, :need_tags_json)
            RETURNING id
            """
        ),
        {
            "user_pk": user_pk,
            "emotion": emotion,
            "intensity": intensity,
            "context_tags_json": json.dumps(context_tags),
            "need_tags_json": json.dumps(need_tags),
        },
    ).mappings().one()

    xp_awarded = 0
    xp_reason = "limite diário já utilizado"
    if daily_checkin_count == 0:
        xp_awarded = 3
        xp_reason = "checkin diario"
        db.execute(
            text(
                """
                INSERT INTO xp_events (user_pk, source_type, source_id, points, reason)
                VALUES (:user_pk, 'checkin', :source_id, :points, :reason)
                """
            ),
            {"user_pk": user_pk, "source_id": str(row["id"]), "points": xp_awarded, "reason": xp_reason}
        )
    db.commit()

    lesson_slug = "emocoes-03-pausa-respiracao" if intensity >= 3 else "emocoes-01-reconhecer"
    return {
        "id": int(row["id"]),
        "xp_awarded": xp_awarded,
        "xp_reason": xp_reason,
        "daily_cap_reached": daily_checkin_count > 0,
        "checkin_date_utc": today_utc,
        "suggestion": {
            "type": "mission_or_lesson",
            "lesson_slug": lesson_slug,
            "cta": "Criar Missão de Apoio",
        },
    }


def list_checkins(db: Session, user_pk: int, range_key: str) -> dict[str, Any]:
    days = 7 if range_key == "week" else 30
    start = datetime.now(UTC) - timedelta(days=days)
    rows = db.execute(
        text(
            """
            SELECT DATE(created_at) as date, emotion, intensity
            FROM emotion_checkins
            WHERE user_pk = :user_pk AND created_at >= :start
            ORDER BY created_at DESC
            """
        ),
        {"user_pk": user_pk, "start": start.isoformat()},
    ).mappings().all()

    return {
        "range": range_key,
        "items": [dict(r) for r in rows],
    }


def build_insights(db: Session, user_pk: int) -> dict[str, Any]:
    start = datetime.now(UTC) - timedelta(days=30)
    rows = db.execute(
        text(
            """
            SELECT emotion, intensity, created_at, need_tags_json
            FROM emotion_checkins
            WHERE user_pk = :user_pk AND created_at >= :start
            ORDER BY created_at DESC
            """
        ),
        {"user_pk": user_pk, "start": start.isoformat()},
    ).mappings().all()

    if not rows:
        return {
            "top_emotions": [],
            "weekly_pattern": "Sem dados suficientes",
            "what_helps": [],
        }

    emotion_counter = Counter()
    weekday_counter = defaultdict(int)
    helps_counter = Counter()

    for row in rows:
        emotion_counter[row["emotion"]] += 1
        dt = datetime.fromisoformat(str(row["created_at"]).replace("Z", "+00:00"))
        weekday_counter[dt.strftime("%A")] += 1
        for tag in json.loads(row["need_tags_json"]):
            helps_counter[tag] += 1

    top_emotions = [k for k, _ in emotion_counter.most_common(2)]
    weekly_pattern = max(weekday_counter.items(), key=lambda pair: pair[1])[0]
    what_helps = [k for k, _ in helps_counter.most_common(3)]

    return {
        "top_emotions": top_emotions,
        "weekly_pattern": f"Maior frequencia em {weekly_pattern}",
        "what_helps": what_helps,
    }
