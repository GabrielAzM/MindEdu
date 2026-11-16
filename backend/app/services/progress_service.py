from __future__ import annotations

import json
import random
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

LEVEL_STEP = 100
MASCOT_STAGE_THRESHOLDS = [10, 30, 50, 70]
RARITY_EFFECT_MULTIPLIER = {"common": 1, "rare": 2, "epic": 3}
COSMETIC_LEVELUP_POOL = [
    {"id": "it_01", "name": "Cachecol Solar", "slot": "neck", "rarity": "common"},
    {"id": "it_02", "name": "Óculos Nebula", "slot": "face", "rarity": "rare"},
    {"id": "it_03", "name": "Chapéu Cometa", "slot": "head", "rarity": "rare"},
    {"id": "it_05", "name": "Aura Verde", "slot": "effect", "rarity": "epic"},
    {"id": "it_07", "name": "Mochila Pixel", "slot": "back", "rarity": "rare"},
    {"id": "it_08", "name": "Tiara Aurora", "slot": "head", "rarity": "epic"},
    {"id": "it_10", "name": "Broche Coração", "slot": "chest", "rarity": "common"},
]

AUTO_TRAIL_BLUEPRINTS = [
    {
        "key": "respira-foco",
        "title": "Sprint de Respiração e Foco",
        "description": "Micropassos de regulação e concentração para dias corridos.",
        "difficulty": "beginner",
        "tags": ["respiracao", "foco", "rotina"],
        "lesson_hints": ["emocoes-03-pausa-respiracao", "emocoes-02-intensidade", "emocoes-07-autocuidado-curto"],
    },
    {
        "key": "comunicacao-calma",
        "title": "Comunicação sem Escalada",
        "description": "Treino curto para conversas difíceis sem conflito tóxico.",
        "difficulty": "intermediate",
        "tags": ["comunicacao", "conflitos", "empatia"],
        "lesson_hints": ["emocoes-06-comunicacao-calma", "emocoes-05-pedir-apoio", "emocoes-04-pensamento-fato"],
    },
    {
        "key": "anti-procrastinacao",
        "title": "Plano Antiprocrastinação",
        "description": "Organização em blocos curtos e revisão de pequenas vitórias.",
        "difficulty": "intermediate",
        "tags": ["foco", "planejamento", "autocuidado"],
        "lesson_hints": ["emocoes-07-autocuidado-curto", "emocoes-02-intensidade", "emocoes-08-plano-dia-dificil"],
    },
    {
        "key": "coragem-social",
        "title": "Missão Coragem Social",
        "description": "Exposição gradual e segura para situações sociais do cotidiano.",
        "difficulty": "advanced",
        "tags": ["social", "coragem", "calma"],
        "lesson_hints": ["emocoes-05-pedir-apoio", "emocoes-06-comunicacao-calma", "emocoes-08-plano-dia-dificil"],
    },
    {
        "key": "uxu-lab",
        "title": "Laboratório de Apoio UxU",
        "description": "Sequência de colaboração útil com foco em feedback seguro.",
        "difficulty": "expert",
        "tags": ["uxu", "empatia", "cooperacao"],
        "lesson_hints": ["emocoes-05-pedir-apoio", "emocoes-06-comunicacao-calma", "emocoes-01-reconhecer"],
    },
    {
        "key": "calma-provas",
        "title": "Calma para Dias de Prova",
        "description": "Rotina de preparo, respiração e revisão sem pânico.",
        "difficulty": "beginner",
        "tags": ["escola", "calma", "foco"],
        "lesson_hints": ["emocoes-02-intensidade", "emocoes-03-pausa-respiracao", "emocoes-08-plano-dia-dificil"],
    },
    {
        "key": "rede-apoio",
        "title": "Rede de Apoio Inteligente",
        "description": "Como pedir ajuda de forma clara para pares e adultos.",
        "difficulty": "intermediate",
        "tags": ["comunicacao", "familia", "escola"],
        "lesson_hints": ["emocoes-05-pedir-apoio", "emocoes-06-comunicacao-calma", "emocoes-01-reconhecer"],
    },
    {
        "key": "energia-diaria",
        "title": "Energia e Ritmo Diário",
        "description": "Micro-hábitos de sono, pausas e foco para constância.",
        "difficulty": "beginner",
        "tags": ["autocuidado", "rotina", "sono"],
        "lesson_hints": ["emocoes-07-autocuidado-curto", "emocoes-03-pausa-respiracao", "emocoes-02-intensidade"],
    },
    {
        "key": "conflitos-respeito",
        "title": "Conflitos com Respeito",
        "description": "Roteiros curtos para resolver conflitos sem ataques.",
        "difficulty": "advanced",
        "tags": ["conflitos", "comunicacao", "empatia"],
        "lesson_hints": ["emocoes-06-comunicacao-calma", "emocoes-04-pensamento-fato", "emocoes-05-pedir-apoio"],
    },
    {
        "key": "autoconfianca-pratica",
        "title": "Autoconfiança na Prática",
        "description": "Evidências reais, metas mínimas e progresso diário.",
        "difficulty": "intermediate",
        "tags": ["autoestima", "coragem", "autocuidado"],
        "lesson_hints": ["emocoes-04-pensamento-fato", "emocoes-07-autocuidado-curto", "emocoes-01-reconhecer"],
    },
    {
        "key": "foco-turbo",
        "title": "Foco Turbo 15x5",
        "description": "Sprints de foco com pausas para manter rendimento.",
        "difficulty": "advanced",
        "tags": ["foco", "estudos", "organizacao"],
        "lesson_hints": ["emocoes-02-intensidade", "emocoes-03-pausa-respiracao", "emocoes-07-autocuidado-curto"],
    },
    {
        "key": "dupla-estrategica",
        "title": "Dupla Estratégica",
        "description": "Trilha para cooperação válida entre parceiros ativos.",
        "difficulty": "expert",
        "tags": ["cooperacao", "uxu", "comunicacao"],
        "lesson_hints": ["emocoes-05-pedir-apoio", "emocoes-06-comunicacao-calma", "emocoes-08-plano-dia-dificil"],
    },
]


def _ordered_blueprints_for_user(user_pk: int) -> list[dict[str, Any]]:
    ordered = [dict(item) for item in AUTO_TRAIL_BLUEPRINTS]
    rng = random.Random(f"blueprints:{user_pk}")
    rng.shuffle(ordered)
    return ordered


def _difficulty_for_xp(base_difficulty: str, total_xp: int, seed: str) -> str:
    rng = random.Random(seed)
    if total_xp >= 650 and base_difficulty in {"beginner", "intermediate"}:
        return rng.choice(["advanced", "expert"])
    if total_xp >= 350 and base_difficulty == "beginner":
        return rng.choice(["intermediate", "advanced"])
    if total_xp < 120 and base_difficulty in {"advanced", "expert"}:
        return "intermediate"
    return base_difficulty


def _pick_lesson_bundle(lesson_ids: list[int], *, seed: str, size: int = 3) -> list[int]:
    if not lesson_ids:
        return []
    desired = min(size, len(lesson_ids))
    pool = list(lesson_ids)
    rng = random.Random(seed)
    rng.shuffle(pool)
    return pool[:desired]


def _bundle_signature(lesson_ids: list[int]) -> tuple[int, ...]:
    return tuple(sorted(lesson_ids))


def _unique_generated_title(title: str, used_titles: set[str]) -> str:
    if title not in used_titles:
        used_titles.add(title)
        return title
    suffix = 2
    while f"{title} ({suffix})" in used_titles:
        suffix += 1
    candidate = f"{title} ({suffix})"
    used_titles.add(candidate)
    return candidate


def _sum_xp(db: Session, user_pk: int) -> int:
    row = db.execute(
        text("SELECT COALESCE(SUM(points), 0) AS total_xp FROM xp_events WHERE user_pk = :user_pk"),
        {"user_pk": user_pk},
    ).mappings().one()
    return int(row["total_xp"])


def _level_from_xp(total_xp: int) -> dict[str, int]:
    level = max(1, (total_xp // LEVEL_STEP) + 1)
    level_start = (level - 1) * LEVEL_STEP
    next_level_at = level * LEVEL_STEP
    current_level_xp = total_xp - level_start
    return {
        "level": level,
        "current_level_xp": current_level_xp,
        "next_level_xp": LEVEL_STEP,
        "xp_to_next": max(0, next_level_at - total_xp),
    }


def _tier_from_xp(total_xp: int) -> str:
    if total_xp >= 700:
        return "Mentor"
    if total_xp >= 300:
        return "Colaborador"
    return "Iniciante"


def _mascot_stage(total_xp: int) -> int:
    stage = 1
    for idx, threshold in enumerate(MASCOT_STAGE_THRESHOLDS, start=1):
        if total_xp >= threshold:
            stage = idx
    return min(stage, 4)


def _ensure_levelup_cosmetic_rewards(db: Session, user_pk: int, total_xp: int) -> dict[str, Any]:
    level = _level_from_xp(total_xp)["level"]
    claimed_levels = {
        int(row["level"])
        for row in db.execute(
            text("SELECT level FROM user_level_reward_claims WHERE user_pk = :user_pk"),
            {"user_pk": user_pk},
        ).mappings().all()
    }
    owned_items = {
        str(row["item_id"])
        for row in db.execute(
            text("SELECT item_id FROM user_mascot_inventory WHERE user_pk = :user_pk"),
            {"user_pk": user_pk},
        ).mappings().all()
    }

    granted: list[dict[str, Any]] = []
    duplicate_xp_total = 0
    for level_idx in range(1, level + 1):
        if level_idx in claimed_levels:
            continue

        rng = random.Random(f"cosmetic:{user_pk}:{level_idx}")
        item = dict(rng.choice(COSMETIC_LEVELUP_POOL))
        duplicate = item["id"] in owned_items
        converted_xp = 0

        if duplicate:
            converted_xp = 5
            duplicate_xp_total += converted_xp
            db.execute(
                text(
                    """
                    INSERT INTO xp_events (user_pk, source_type, source_id, points, reason)
                    VALUES (:user_pk, 'admin_adjustment', :source_id, :points, :reason)
                    """
                ),
                {
                    "user_pk": user_pk,
                    "source_id": f"cosmetic-level-{level_idx}",
                    "points": converted_xp,
                    "reason": "cosmetico repetido convertido em XP",
                },
            )
        else:
            db.execute(
                text(
                    """
                    INSERT INTO user_mascot_inventory (user_pk, item_id, item_name, rarity, slot, obtained_from)
                    VALUES (:user_pk, :item_id, :item_name, :rarity, :slot, 'levelup')
                    """
                ),
                {
                    "user_pk": user_pk,
                    "item_id": item["id"],
                    "item_name": item["name"],
                    "rarity": item["rarity"],
                    "slot": item["slot"],
                },
            )
            owned_items.add(str(item["id"]))
            granted.append(
                {
                    "level": level_idx,
                    **item,
                    "effect_multiplier": RARITY_EFFECT_MULTIPLIER[item["rarity"]],
                }
            )

        db.execute(
            text(
                """
                INSERT INTO user_level_reward_claims (user_pk, level, item_id, duplicate_converted, converted_xp)
                VALUES (:user_pk, :level, :item_id, :duplicate_converted, :converted_xp)
                """
            ),
            {
                "user_pk": user_pk,
                "level": level_idx,
                "item_id": item["id"],
                "duplicate_converted": 1 if duplicate else 0,
                "converted_xp": converted_xp,
            },
        )

    return {
        "granted": granted,
        "duplicate_xp_total": duplicate_xp_total,
    }


def _inventory_for_user(db: Session, user_pk: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT item_id, item_name, rarity, slot, obtained_from, obtained_at
            FROM user_mascot_inventory
            WHERE user_pk = :user_pk
            ORDER BY obtained_at ASC, id ASC
            """
        ),
        {"user_pk": user_pk},
    ).mappings().all()
    return [
        {
            "id": str(row["item_id"]),
            "name": str(row["item_name"]),
            "rarity": str(row["rarity"]),
            "slot": str(row["slot"]),
            "obtained_from": str(row["obtained_from"]),
            "obtained_at": str(row["obtained_at"]),
            "effect_multiplier": RARITY_EFFECT_MULTIPLIER.get(str(row["rarity"]), 1),
        }
        for row in rows
    ]


def _equipped_for_user(db: Session, user_pk: int, inventory: list[dict[str, Any]]) -> dict[str, Any]:
    inventory_by_id = {str(item["id"]): item for item in inventory}
    equipped_rows = db.execute(
        text(
            """
            SELECT mascot_id, item_id
            FROM user_mascot_equipment
            WHERE user_pk = :user_pk
            """
        ),
        {"user_pk": user_pk},
    ).mappings().all()
    equipped_ids = {"fox": None, "owl": None}
    for row in equipped_rows:
        mascot_id = str(row["mascot_id"])
        item_id = str(row["item_id"]) if row["item_id"] else None
        if mascot_id in equipped_ids:
            equipped_ids[mascot_id] = item_id

    equipped_items = {
        mascot_id: (inventory_by_id[item_id] if item_id and item_id in inventory_by_id else None)
        for mascot_id, item_id in equipped_ids.items()
    }

    return {
        "ids": equipped_ids,
        "items": equipped_items,
    }


def _recent_xp_chart(db: Session, user_pk: int) -> list[dict[str, Any]]:
    start = datetime.now(UTC) - timedelta(days=6)
    rows = db.execute(
        text(
            """
            SELECT DATE(created_at) AS day, COALESCE(SUM(points), 0) AS points
            FROM xp_events
            WHERE user_pk = :user_pk AND created_at >= :start
            GROUP BY DATE(created_at)
            ORDER BY day
            """
        ),
        {"user_pk": user_pk, "start": start.isoformat()},
    ).mappings().all()

    points_by_day = {str(r["day"]): int(r["points"]) for r in rows}
    chart: list[dict[str, Any]] = []
    for offset in range(7):
        day = (start + timedelta(days=offset)).date().isoformat()
        chart.append({"day": day, "xp": points_by_day.get(day, 0)})
    return chart


def _skill_breakdown(db: Session, user_pk: int) -> dict[str, int]:
    rows = db.execute(
        text(
            """
            SELECT source_type, COALESCE(SUM(points), 0) AS points
            FROM xp_events
            WHERE user_pk = :user_pk
            GROUP BY source_type
            """
        ),
        {"user_pk": user_pk},
    ).mappings().all()

    skill_points = defaultdict(int)
    for row in rows:
        source = str(row["source_type"])
        points = int(row["points"])
        if source in {"mission_response_useful", "coop"}:
            skill_points["empatia"] += points
            skill_points["comunicacao"] += points // 2
        elif source in {"checkin"}:
            skill_points["calma"] += points
            skill_points["autocuidado"] += points
        elif source in {"quiz", "lesson", "challenge"}:
            skill_points["coragem"] += points // 2
            skill_points["autocuidado"] += points // 2

    return {
        "empatia": int(skill_points["empatia"]),
        "calma": int(skill_points["calma"]),
        "comunicacao": int(skill_points["comunicacao"]),
        "coragem": int(skill_points["coragem"]),
        "autocuidado": int(skill_points["autocuidado"]),
    }


def ensure_generated_trails(db: Session, user_pk: int, total_xp: int) -> None:
    target_count = min(10, max(2, 1 + total_xp // 120))
    current = int(
        db.execute(
            text("SELECT COUNT(*) FROM generated_trails WHERE user_pk = :user_pk AND status = 'active'"),
            {"user_pk": user_pk},
        ).scalar_one()
    )

    if current >= target_count:
        return

    lesson_rows = db.execute(
        text("SELECT id, slug FROM lessons WHERE is_active = 1 ORDER BY id"),
    ).mappings().all()
    lesson_ids = [
        int(row["id"])
        for row in lesson_rows
    ]
    lesson_id_by_slug = {
        str(row["slug"]): int(row["id"])
        for row in db.execute(
            text("SELECT id, slug FROM lessons WHERE is_active = 1 ORDER BY id"),
        ).mappings().all()
    }
    if not lesson_ids:
        return

    ordered_blueprints = _ordered_blueprints_for_user(user_pk)
    used_titles = {
        str(row["title"])
        for row in db.execute(
            text("SELECT title FROM generated_trails WHERE user_pk = :user_pk"),
            {"user_pk": user_pk},
        ).mappings().all()
    }
    used_lessons = set()
    used_bundle_signatures: set[tuple[int, ...]] = set()
    for row in db.execute(
        text("SELECT lesson_bundle_json FROM generated_trails WHERE user_pk = :user_pk AND status = 'active'"),
        {"user_pk": user_pk},
    ).mappings().all():
        bundle_ids: list[int] = []
        for value in json.loads(row["lesson_bundle_json"] or "[]"):
            if isinstance(value, int):
                bundle_ids.append(value)
            elif isinstance(value, str) and value.isdigit():
                bundle_ids.append(int(value))
        for lesson_id in bundle_ids:
            used_lessons.add(lesson_id)
        if bundle_ids:
            used_bundle_signatures.add(_bundle_signature(bundle_ids))

    for idx in range(current, target_count):
        blueprint = ordered_blueprints[idx % len(ordered_blueprints)]
        trail_key = f"xp-{(total_xp // 120) + 1}-{idx + 1}-{blueprint['key']}"
        difficulty = _difficulty_for_xp(str(blueprint["difficulty"]), total_xp, f"diff:{user_pk}:{idx}:{total_xp}")
        hinted_ids = [
            lesson_id_by_slug[slug]
            for slug in blueprint.get("lesson_hints", [])
            if isinstance(slug, str) and slug in lesson_id_by_slug
        ]
        lesson_bundle: list[int] = []
        for attempt in range(12):
            hinted_pool = [lesson_id for lesson_id in hinted_ids if lesson_id not in used_lessons]
            if len(hinted_pool) < 2:
                hinted_pool = hinted_ids
            generic_pool = [lesson_id for lesson_id in lesson_ids if lesson_id not in used_lessons and lesson_id not in hinted_pool]
            if len(generic_pool) < 1:
                generic_pool = [lesson_id for lesson_id in lesson_ids if lesson_id not in hinted_pool]
            candidate_pool = hinted_pool + generic_pool
            if len(candidate_pool) < 3:
                candidate_pool = hinted_ids + lesson_ids

            picked = _pick_lesson_bundle(candidate_pool, seed=f"bundle:{user_pk}:{idx}:{total_xp}:{attempt}")
            lesson_bundle = []
            for lesson_id in picked:
                if lesson_id not in lesson_bundle:
                    lesson_bundle.append(lesson_id)
            while len(lesson_bundle) < min(3, len(lesson_ids)):
                fallback = next((item for item in lesson_ids if item not in lesson_bundle), None)
                if fallback is None:
                    break
                lesson_bundle.append(fallback)
            signature = _bundle_signature(lesson_bundle)
            if signature not in used_bundle_signatures:
                used_bundle_signatures.add(signature)
                break
        if not lesson_bundle:
            lesson_bundle = _pick_lesson_bundle(lesson_ids, seed=f"bundle-fallback:{user_pk}:{idx}:{total_xp}")
        for lesson_id in lesson_bundle:
            used_lessons.add(lesson_id)
        title = _unique_generated_title(str(blueprint["title"]), used_titles)

        db.execute(
            text(
                """
                INSERT OR IGNORE INTO generated_trails (
                  user_pk, trail_key, title, description, difficulty, focus_tags_json, lesson_bundle_json, recommended_xp, status
                ) VALUES (
                  :user_pk, :trail_key, :title, :description, :difficulty, :focus_tags_json, :lesson_bundle_json, :recommended_xp, 'active'
                )
                """
            ),
            {
                "user_pk": user_pk,
                "trail_key": trail_key,
                "title": title,
                "description": str(blueprint["description"]),
                "difficulty": difficulty,
                "focus_tags_json": json.dumps(blueprint["tags"]),
                "lesson_bundle_json": json.dumps(lesson_bundle),
                "recommended_xp": total_xp,
            },
        )

    db.commit()


def list_user_trails(db: Session, user_pk: int) -> list[dict[str, Any]]:
    total_xp = _sum_xp(db, user_pk)
    reward_summary = _ensure_levelup_cosmetic_rewards(db, user_pk, total_xp)
    if reward_summary["granted"] or reward_summary["duplicate_xp_total"] > 0:
        db.commit()
        total_xp = _sum_xp(db, user_pk)
    ensure_generated_trails(db, user_pk, total_xp)
    completed_lesson_ids = {
        int(row["lesson_id"])
        for row in db.execute(
            text("SELECT lesson_id FROM lesson_completion WHERE user_pk = :user_pk"),
            {"user_pk": user_pk},
        ).mappings().all()
    }

    static_rows = db.execute(
        text(
            """
            SELECT
              t.id,
              t.slug,
              t.title,
              t.description,
              t.age_group,
              COUNT(l.id) AS lesson_count,
              MIN(l.id) AS first_lesson_id
            FROM trails t
            LEFT JOIN lessons l ON l.trail_id = t.id AND l.is_active = 1
            WHERE t.is_active = 1
            GROUP BY t.id
            ORDER BY t.id
            """
        )
    ).mappings().all()

    generated_rows = db.execute(
        text(
            """
            SELECT id, trail_key, title, description, difficulty, focus_tags_json, lesson_bundle_json, status, recommended_xp, created_at
            FROM generated_trails
            WHERE user_pk = :user_pk
            ORDER BY created_at DESC
            """
        ),
        {"user_pk": user_pk},
    ).mappings().all()
    fallback_first_lesson = db.execute(
        text("SELECT MIN(id) FROM lessons WHERE is_active = 1")
    ).scalar_one()

    items: list[dict[str, Any]] = []
    for row in static_rows:
        item = dict(row)
        item["is_generated"] = False
        item["difficulty"] = "core"
        item["focus_tags"] = []
        items.append(item)

    seen_generated_titles: set[str] = set()
    seen_generated_signatures: set[tuple[int, ...]] = set()
    for row in generated_rows:
        title = str(row["title"])
        if title in seen_generated_titles:
            continue

        bundle_raw = json.loads(row["lesson_bundle_json"])
        lesson_bundle_ids: list[int] = []
        for value in bundle_raw:
            if isinstance(value, int):
                lesson_bundle_ids.append(value)
                continue
            if isinstance(value, str) and value.isdigit():
                lesson_bundle_ids.append(int(value))
        bundle_signature = _bundle_signature(lesson_bundle_ids)
        if bundle_signature in seen_generated_signatures:
            continue
        seen_generated_signatures.add(bundle_signature)
        seen_generated_titles.add(title)

        if lesson_bundle_ids and all(lesson_id in completed_lesson_ids for lesson_id in lesson_bundle_ids):
            if str(row["status"]) != "completed":
                db.execute(
                    text("UPDATE generated_trails SET status = 'completed' WHERE id = :id"),
                    {"id": int(row["id"])},
                )
            continue

        lesson_meta_rows = []
        if lesson_bundle_ids:
            placeholders = ",".join([str(lesson_id) for lesson_id in lesson_bundle_ids])
            lesson_meta_rows = db.execute(
                text(
                    f"""
                    SELECT id, title, slug
                    FROM lessons
                    WHERE id IN ({placeholders})
                    ORDER BY position
                    """
                )
            ).mappings().all()
        lessons_preview = [
            {"id": int(meta["id"]), "title": str(meta["title"]), "slug": str(meta["slug"])}
            for meta in lesson_meta_rows
        ]
        first_pending_lesson = next((lesson_id for lesson_id in lesson_bundle_ids if lesson_id not in completed_lesson_ids), None)
        first_lesson_id = first_pending_lesson if first_pending_lesson is not None else (lesson_bundle_ids[0] if lesson_bundle_ids else fallback_first_lesson)
        focus_tags = json.loads(row["focus_tags_json"])
        mission_suggestion = focus_tags[0] if focus_tags else None

        item = {
            "id": int(row["id"]),
            "slug": str(row["trail_key"]),
            "title": title,
            "description": str(row["description"]),
            "age_group": "10-12",
            "lesson_count": len(lesson_bundle_ids),
            "first_lesson_id": first_lesson_id,
            "is_generated": True,
            "difficulty": row["difficulty"],
            "focus_tags": focus_tags,
            "recommended_xp": int(row["recommended_xp"]),
            "status": row["status"],
            "lesson_ids": lesson_bundle_ids,
            "lessons_preview": lessons_preview,
            "mission_suggestion": mission_suggestion,
        }
        items.append(item)

    db.commit()
    return items


def equip_mascot_item(db: Session, user_pk: int, mascot_id: str, item_id: str | None) -> dict[str, Any]:
    if mascot_id not in {"fox", "owl"}:
        raise ValueError("mascot_id invalido")

    if item_id is None:
        db.execute(
            text(
                """
                INSERT INTO user_mascot_equipment (user_pk, mascot_id, item_id)
                VALUES (:user_pk, :mascot_id, NULL)
                ON CONFLICT(user_pk, mascot_id) DO UPDATE SET item_id = NULL, equipped_at = CURRENT_TIMESTAMP
                """
            ),
            {"user_pk": user_pk, "mascot_id": mascot_id},
        )
        db.commit()
        return {
            "mascot_id": mascot_id,
            "equipped_item": None,
            "effect_multiplier": 0,
        }

    item_row = db.execute(
        text(
            """
            SELECT item_id, item_name, rarity, slot
            FROM user_mascot_inventory
            WHERE user_pk = :user_pk AND item_id = :item_id
            LIMIT 1
            """
        ),
        {"user_pk": user_pk, "item_id": item_id},
    ).mappings().first()
    if not item_row:
        raise PermissionError("O item não pertence ao usuário.")

    db.execute(
        text(
            """
            INSERT INTO user_mascot_equipment (user_pk, mascot_id, item_id)
            VALUES (:user_pk, :mascot_id, :item_id)
            ON CONFLICT(user_pk, mascot_id) DO UPDATE SET item_id = excluded.item_id, equipped_at = CURRENT_TIMESTAMP
            """
        ),
        {"user_pk": user_pk, "mascot_id": mascot_id, "item_id": item_id},
    )
    db.commit()

    rarity = str(item_row["rarity"])
    return {
        "mascot_id": mascot_id,
        "equipped_item": {
            "id": str(item_row["item_id"]),
            "name": str(item_row["item_name"]),
            "rarity": rarity,
            "slot": str(item_row["slot"]),
        },
        "effect_multiplier": RARITY_EFFECT_MULTIPLIER.get(rarity, 1),
    }


def get_educator_progress_summary(db: Session, user_pk: int) -> dict[str, Any]:
    user = db.execute(
        text("SELECT user_id, username FROM users WHERE id = :id AND role = 'user'"),
        {"id": user_pk},
    ).mappings().first()
    if not user:
        raise ValueError("user not found")

    total_xp = _sum_xp(db, user_pk)
    progress = {
        "lessons_completed": int(
            db.execute(
                text("SELECT COUNT(*) FROM lesson_completion WHERE user_pk = :user_pk"),
                {"user_pk": user_pk},
            ).scalar_one()
        ),
        "quizzes_passed": int(
            db.execute(
                text("SELECT COUNT(*) FROM quiz_attempts WHERE user_pk = :user_pk AND score >= 70"),
                {"user_pk": user_pk},
            ).scalar_one()
        ),
        "challenges_completed": int(
            db.execute(
                text("SELECT COUNT(*) FROM challenge_completion WHERE user_pk = :user_pk AND status = 'completed'"),
                {"user_pk": user_pk},
            ).scalar_one()
        ),
        "missions_created": int(
            db.execute(
                text("SELECT COUNT(*) FROM missions WHERE creator_user_pk = :user_pk"),
                {"user_pk": user_pk},
            ).scalar_one()
        ),
        "helpful_responses": int(
            db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM mission_feedback mf
                    JOIN mission_responses mr ON mr.id = mf.response_id
                    WHERE mr.responder_user_pk = :user_pk AND mf.is_useful = 1
                    """
                ),
                {"user_pk": user_pk},
            ).scalar_one()
        ),
    }

    return {
        "user": dict(user),
        "xp": {"total": total_xp, **_level_from_xp(total_xp), "tier": _tier_from_xp(total_xp)},
        "progress": progress,
        "skills": _skill_breakdown(db, user_pk),
        "mascot": {"stage": _mascot_stage(total_xp), "max_stage": 4},
        "recent_xp": _recent_xp_chart(db, user_pk),
    }


def get_profile_summary(db: Session, user_pk: int) -> dict[str, Any]:
    user = db.execute(
        text("SELECT user_id, username, role, status FROM users WHERE id = :id"),
        {"id": user_pk},
    ).mappings().first()
    if not user:
        raise ValueError("user not found")

    total_xp = _sum_xp(db, user_pk)
    reward_summary = _ensure_levelup_cosmetic_rewards(db, user_pk, total_xp)
    total_xp = _sum_xp(db, user_pk)
    level = _level_from_xp(total_xp)

    lessons_completed = int(
        db.execute(text("SELECT COUNT(*) FROM lesson_completion WHERE user_pk = :user_pk"), {"user_pk": user_pk}).scalar_one()
    )
    quizzes_passed = int(
        db.execute(
            text("SELECT COUNT(*) FROM quiz_attempts WHERE user_pk = :user_pk AND score >= 70"),
            {"user_pk": user_pk},
        ).scalar_one()
    )
    missions_created = int(
        db.execute(text("SELECT COUNT(*) FROM missions WHERE creator_user_pk = :user_pk"), {"user_pk": user_pk}).scalar_one()
    )
    helpful_responses = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM mission_feedback mf
                JOIN mission_responses mr ON mr.id = mf.response_id
                WHERE mr.responder_user_pk = :user_pk AND mf.is_useful = 1
                """
            ),
            {"user_pk": user_pk},
        ).scalar_one()
    )
    coop_pairs_active = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM coop_pairs
                WHERE status = 'active' AND (user_low_pk = :user_pk OR user_high_pk = :user_pk)
                """
            ),
            {"user_pk": user_pk},
        ).scalar_one()
    )

    static_trails_done = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT l.trail_id, COUNT(*) AS total_lessons
                    FROM lessons l
                    WHERE l.is_active = 1
                    GROUP BY l.trail_id
                ) totals
                JOIN (
                    SELECT l.trail_id, COUNT(*) AS done_lessons
                    FROM lesson_completion lc
                    JOIN lessons l ON l.id = lc.lesson_id
                    WHERE lc.user_pk = :user_pk
                    GROUP BY l.trail_id
                ) done ON done.trail_id = totals.trail_id
                WHERE done.done_lessons >= totals.total_lessons
                """
            ),
            {"user_pk": user_pk},
        ).scalar_one()
    )
    generated_trails_done = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM generated_trails
                WHERE user_pk = :user_pk AND status = 'completed'
                """
            ),
            {"user_pk": user_pk},
        ).scalar_one()
    )
    trails_done = static_trails_done + generated_trails_done

    mascot_stage = _mascot_stage(total_xp)
    inventory = _inventory_for_user(db, user_pk)
    equipped = _equipped_for_user(db, user_pk, inventory)
    if reward_summary["granted"] or reward_summary["duplicate_xp_total"] > 0:
        db.commit()
    return {
        "user": dict(user),
        "xp": {
            "total": total_xp,
            **level,
            "tier": _tier_from_xp(total_xp),
        },
        "progress": {
            "trails_completed": trails_done,
            "lessons_completed": lessons_completed,
            "quizzes_passed": quizzes_passed,
            "missions_created": missions_created,
            "helpful_responses": helpful_responses,
            "coop_pairs_active": coop_pairs_active,
        },
        "skills": _skill_breakdown(db, user_pk),
        "mascot": {
            "stage": mascot_stage,
            "max_stage": 4,
            "evolution_name": f"Evolução {mascot_stage}",
            "next_stage_at": MASCOT_STAGE_THRESHOLDS[min(3, mascot_stage)] if mascot_stage < 4 else None,
        },
        "cosmetics": {
            "reward_pool_total": len(COSMETIC_LEVELUP_POOL),
            "inventory": inventory,
            "equipped": equipped["ids"],
            "equipped_items": equipped["items"],
            "rarity_effect_multiplier": RARITY_EFFECT_MULTIPLIER,
            "new_rewards": reward_summary["granted"],
            "duplicate_xp_converted": reward_summary["duplicate_xp_total"],
        },
        "recent_xp": _recent_xp_chart(db, user_pk),
    }


def get_home_dashboard(db: Session, user_pk: int) -> dict[str, Any]:
    profile = get_profile_summary(db, user_pk)
    trail_items = list_user_trails(db, user_pk)

    generated_active = [item for item in trail_items if item.get("is_generated")]
    next_recommended = generated_active[0] if generated_active else None

    return {
        "headline": {
            "xp_total": profile["xp"]["total"],
            "level": profile["xp"]["level"],
            "tier": profile["xp"]["tier"],
            "xp_to_next": profile["xp"]["xp_to_next"],
        },
        "stats": profile["progress"],
        "skills": profile["skills"],
        "mascot": profile["mascot"],
        "recent_xp": profile["recent_xp"],
        "next_generated_trail": next_recommended,
    }
