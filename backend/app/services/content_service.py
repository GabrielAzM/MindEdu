from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session

SEEDS_DIR = Path("backend/seeds")


def seed_initial_content(db: Session) -> None:
    seed_support_cards(db)
    sync_trail_emotions_curriculum(db)


def seed_support_cards(db: Session) -> None:
    path = SEEDS_DIR / "support_cards.json"
    if not path.exists():
        path = Path(__file__).resolve().parents[2] / "seeds" / "support_cards.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    for card in data["cards"]:
        db.execute(
            text(
                """
                INSERT INTO support_cards (card_key, category, tone, title, body, guided_actions_json, is_active)
                VALUES (:card_key, :category, :tone, :title, :body, :guided_actions_json, 1)
                ON CONFLICT(card_key) DO UPDATE SET
                  category = excluded.category,
                  tone = excluded.tone,
                  title = excluded.title,
                  body = excluded.body,
                  guided_actions_json = excluded.guided_actions_json,
                  is_active = 1
                """
            ),
            {
                "card_key": card["card_key"],
                "category": card["category"],
                "tone": card["tone"],
                "title": card["title"],
                "body": card["body"],
                "guided_actions_json": json.dumps(card["guided_actions"]),
            },
        )
    db.commit()


def _load_emotions_seed() -> dict[str, Any]:
    path = SEEDS_DIR / "trails_emotions.json"
    if not path.exists():
        path = Path(__file__).resolve().parents[2] / "seeds" / "trails_emotions.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _replace_quiz_questions(db: Session, quiz_id: int, questions: list[dict[str, Any]]) -> None:
    existing_question_rows = db.execute(
        text("SELECT id FROM quiz_questions WHERE quiz_id = :quiz_id"),
        {"quiz_id": quiz_id},
    ).mappings().all()
    existing_question_ids = [int(row["id"]) for row in existing_question_rows]
    if existing_question_ids:
        placeholders = ",".join([str(qid) for qid in existing_question_ids])
        db.execute(text(f"DELETE FROM quiz_options WHERE question_id IN ({placeholders})"))
        db.execute(text("DELETE FROM quiz_questions WHERE quiz_id = :quiz_id"), {"quiz_id": quiz_id})

    for q_idx, question in enumerate(questions, start=1):
        question_row = db.execute(
            text(
                """
                INSERT INTO quiz_questions (quiz_id, position, prompt, explanation)
                VALUES (:quiz_id, :position, :prompt, :explanation)
                RETURNING id
                """
            ),
            {
                "quiz_id": quiz_id,
                "position": q_idx,
                "prompt": question["prompt"],
                "explanation": question["explanation"],
            },
        ).mappings().one()
        question_id = int(question_row["id"])

        for o_idx, option in enumerate(question["options"], start=1):
            db.execute(
                text(
                    """
                    INSERT INTO quiz_options (question_id, position, option_text, is_correct)
                    VALUES (:question_id, :position, :option_text, :is_correct)
                    """
                ),
                {
                    "question_id": question_id,
                    "position": o_idx,
                    "option_text": option["text"],
                    "is_correct": 1 if option["is_correct"] else 0,
                },
            )


def sync_trail_emotions_curriculum(db: Session) -> None:
    payload = _load_emotions_seed()

    trail = payload["trail"]
    trail_row = db.execute(
        text("SELECT id FROM trails WHERE slug = :slug"),
        {"slug": trail["slug"]},
    ).mappings().first()
    if not trail_row:
        trail_row = db.execute(
            text(
                """
                INSERT INTO trails (slug, title, description, age_group, is_active)
                VALUES (:slug, :title, :description, :age_group, 1)
                RETURNING id
                """
            ),
            {
                "slug": trail["slug"],
                "title": trail["title"],
                "description": trail["description"],
                "age_group": trail["age_group"],
            },
        ).mappings().one()
    trail_id = int(trail_row["id"])
    db.execute(
        text(
            """
            UPDATE trails
            SET title = :title, description = :description, age_group = :age_group, is_active = 1
            WHERE id = :id
            """
        ),
        {
            "title": trail["title"],
            "description": trail["description"],
            "age_group": trail["age_group"],
            "id": trail_id,
        },
    )

    lesson_slugs: list[str] = []
    quiz_slugs: list[str] = []
    challenge_slugs: list[str] = []

    for idx, lesson in enumerate(payload["lessons"], start=1):
        lesson_slugs.append(lesson["slug"])
        lesson_row = db.execute(
            text("SELECT id FROM lessons WHERE slug = :slug"),
            {"slug": lesson["slug"]},
        ).mappings().first()
        if lesson_row:
            lesson_id = int(lesson_row["id"])
            db.execute(
                text(
                    """
                    UPDATE lessons
                    SET trail_id = :trail_id,
                        title = :title,
                        position = :position,
                        duration_min = :duration_min,
                        cards_json = :cards_json,
                        is_active = 1
                    WHERE id = :id
                    """
                ),
                {
                    "trail_id": trail_id,
                    "title": lesson["title"],
                    "position": idx,
                    "duration_min": lesson["duration_min"],
                    "cards_json": json.dumps(lesson["cards"]),
                    "id": lesson_id,
                },
            )
        else:
            lesson_row = db.execute(
                text(
                    """
                    INSERT INTO lessons (trail_id, slug, title, position, duration_min, cards_json, is_active)
                    VALUES (:trail_id, :slug, :title, :position, :duration_min, :cards_json, 1)
                    RETURNING id
                    """
                ),
                {
                    "trail_id": trail_id,
                    "slug": lesson["slug"],
                    "title": lesson["title"],
                    "position": idx,
                    "duration_min": lesson["duration_min"],
                    "cards_json": json.dumps(lesson["cards"]),
                },
            ).mappings().one()
            lesson_id = int(lesson_row["id"])

        quiz = lesson["quiz"]
        quiz_slugs.append(quiz["slug"])
        quiz_row = db.execute(
            text("SELECT id FROM quizzes WHERE slug = :slug"),
            {"slug": quiz["slug"]},
        ).mappings().first()
        if quiz_row:
            quiz_id = int(quiz_row["id"])
            db.execute(
                text(
                    """
                    UPDATE quizzes
                    SET trail_id = :trail_id,
                        lesson_id = :lesson_id,
                        title = :title,
                        passing_score = 70,
                        is_active = 1
                    WHERE id = :id
                    """
                ),
                {
                    "trail_id": trail_id,
                    "lesson_id": lesson_id,
                    "title": quiz["title"],
                    "id": quiz_id,
                },
            )
        else:
            quiz_row = db.execute(
                text(
                    """
                    INSERT INTO quizzes (trail_id, lesson_id, slug, title, passing_score, is_active)
                    VALUES (:trail_id, :lesson_id, :slug, :title, 70, 1)
                    RETURNING id
                    """
                ),
                {
                    "trail_id": trail_id,
                    "lesson_id": lesson_id,
                    "slug": quiz["slug"],
                    "title": quiz["title"],
                },
            ).mappings().one()
            quiz_id = int(quiz_row["id"])

        _replace_quiz_questions(db, quiz_id=quiz_id, questions=quiz["questions"])

        challenge = lesson["challenge"]
        challenge_slugs.append(challenge["slug"])
        challenge_row = db.execute(
            text("SELECT id FROM challenges WHERE slug = :slug"),
            {"slug": challenge["slug"]},
        ).mappings().first()
        if challenge_row:
            db.execute(
                text(
                    """
                    UPDATE challenges
                    SET trail_id = :trail_id,
                        lesson_id = :lesson_id,
                        title = :title,
                        steps_json = :steps_json,
                        safety_notes_json = :safety_notes_json,
                        xp_reward = 20,
                        is_active = 1
                    WHERE id = :id
                    """
                ),
                {
                    "trail_id": trail_id,
                    "lesson_id": lesson_id,
                    "title": challenge["title"],
                    "steps_json": json.dumps(challenge["steps"]),
                    "safety_notes_json": json.dumps(challenge["safety_notes"]),
                    "id": int(challenge_row["id"]),
                },
            )
        else:
            db.execute(
                text(
                    """
                    INSERT INTO challenges (trail_id, lesson_id, slug, title, steps_json, safety_notes_json, xp_reward, is_active)
                    VALUES (:trail_id, :lesson_id, :slug, :title, :steps_json, :safety_notes_json, 20, 1)
                    """
                ),
                {
                    "trail_id": trail_id,
                    "lesson_id": lesson_id,
                    "slug": challenge["slug"],
                    "title": challenge["title"],
                    "steps_json": json.dumps(challenge["steps"]),
                    "safety_notes_json": json.dumps(challenge["safety_notes"]),
                },
            )

    if lesson_slugs:
        quoted_slugs = ",".join([f"'{slug}'" for slug in lesson_slugs])
        db.execute(text(f"UPDATE lessons SET is_active = 0 WHERE trail_id = :trail_id AND slug NOT IN ({quoted_slugs})"), {"trail_id": trail_id})
    if quiz_slugs:
        quoted_quiz_slugs = ",".join([f"'{slug}'" for slug in quiz_slugs])
        db.execute(text(f"UPDATE quizzes SET is_active = 0 WHERE trail_id = :trail_id AND slug NOT IN ({quoted_quiz_slugs})"), {"trail_id": trail_id})
    if challenge_slugs:
        quoted_challenge_slugs = ",".join([f"'{slug}'" for slug in challenge_slugs])
        db.execute(text(f"UPDATE challenges SET is_active = 0 WHERE trail_id = :trail_id AND slug NOT IN ({quoted_challenge_slugs})"), {"trail_id": trail_id})

    db.commit()


def list_trails(db: Session, age_group: str | None = None) -> list[dict[str, Any]]:
    query = """
      SELECT t.id, t.slug, t.title, t.description, t.age_group,
             COUNT(l.id) AS lesson_count,
             MIN(l.id) AS first_lesson_id
      FROM trails t
      LEFT JOIN lessons l ON l.trail_id = t.id
      WHERE t.is_active = 1
    """
    params: dict[str, Any] = {}
    if age_group:
        query += " AND (t.age_group = :age_group OR t.age_group = 'all')"
        params["age_group"] = age_group
    query += " GROUP BY t.id ORDER BY t.id"

    rows = db.execute(text(query), params).mappings().all()
    return [dict(row) for row in rows]


def list_user_challenges(db: Session, user_pk: int) -> list[dict[str, Any]]:
    rows = db.execute(
        text(
            """
            SELECT
              c.id,
              c.title,
              c.xp_reward,
              c.safety_notes_json,
              l.id AS lesson_id,
              l.title AS lesson_title,
              (
                SELECT q.id
                FROM quizzes q
                WHERE q.lesson_id = l.id AND q.is_active = 1
                ORDER BY q.id
                LIMIT 1
              ) AS quiz_id,
              cc.status,
              cc.completed_at
            FROM challenges c
            JOIN lessons l ON l.id = c.lesson_id AND l.is_active = 1
            LEFT JOIN challenge_completion cc
              ON cc.challenge_id = c.id AND cc.user_pk = :user_pk
            WHERE c.is_active = 1
            ORDER BY l.position, c.id
            """
        ),
        {"user_pk": user_pk},
    ).mappings().all()

    return [
        {
            "id": int(row["id"]),
            "title": str(row["title"]),
            "xp_reward": int(row["xp_reward"]),
            "safety_notes": json.loads(row["safety_notes_json"] or "[]"),
            "lesson_id": int(row["lesson_id"]),
            "lesson_title": str(row["lesson_title"]),
            "quiz_id": int(row["quiz_id"]) if row["quiz_id"] is not None else None,
            "status": str(row["status"]) if row["status"] else "pending",
            "completed_at": str(row["completed_at"]) if row["completed_at"] else None,
            "completed": row["status"] == "completed",
        }
        for row in rows
    ]


def get_lesson(db: Session, lesson_id: int) -> dict | None:
    row = db.execute(
        text(
            """
            SELECT
              l.id,
              l.slug,
              l.title,
              l.duration_min,
              l.cards_json,
              (
                SELECT q.id
                FROM quizzes q
                WHERE q.lesson_id = l.id AND q.is_active = 1
                ORDER BY q.id
                LIMIT 1
              ) AS quiz_id
            FROM lessons
            l
            WHERE l.id = :lesson_id AND l.is_active = 1
            """
        ),
        {"lesson_id": lesson_id},
    ).mappings().first()
    if not row:
        return None
    lesson = dict(row)
    lesson["cards"] = json.loads(lesson.pop("cards_json"))
    return lesson


def complete_lesson(db: Session, user_pk: int, lesson_id: int, seconds_spent: int = 0) -> dict[str, Any]:
    lesson = db.execute(
        text("SELECT id FROM lessons WHERE id = :lesson_id AND is_active = 1"),
        {"lesson_id": lesson_id},
    ).mappings().first()
    if not lesson:
        raise ValueError("lesson not found")

    existing = db.execute(
        text("SELECT id FROM lesson_completion WHERE user_pk = :user_pk AND lesson_id = :lesson_id"),
        {"user_pk": user_pk, "lesson_id": lesson_id},
    ).mappings().first()

    if existing:
        db.execute(
            text(
                """
                UPDATE lesson_completion
                SET seconds_spent = seconds_spent + :seconds_spent, completed_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """
            ),
            {
                "id": existing["id"],
                "seconds_spent": max(0, seconds_spent),
            },
        )
        db.commit()
        return {"status": "already_completed", "xp_awarded": 0}

    db.execute(
        text(
            """
            INSERT INTO lesson_completion (user_pk, lesson_id, seconds_spent, completed_at)
            VALUES (:user_pk, :lesson_id, :seconds_spent, CURRENT_TIMESTAMP)
            """
        ),
        {
            "user_pk": user_pk,
            "lesson_id": lesson_id,
            "seconds_spent": max(0, seconds_spent),
        },
    )
    db.execute(
        text(
            """
            INSERT INTO xp_events (user_pk, source_type, source_id, points, reason)
            VALUES (:user_pk, 'lesson', :source_id, 12, 'lesson completion')
            """
        ),
        {
            "user_pk": user_pk,
            "source_id": str(lesson_id),
        },
    )
    db.commit()
    return {"status": "completed", "xp_awarded": 12}


def get_quiz(db: Session, quiz_id: int) -> dict[str, Any] | None:
    quiz = db.execute(
        text(
            """
            SELECT
              q.id,
              q.slug,
              q.title,
              q.passing_score,
              q.lesson_id,
              q.trail_id,
              l.title AS lesson_title,
              l.cards_json AS lesson_cards_json,
              t.title AS trail_title
            FROM quizzes q
            LEFT JOIN lessons l ON l.id = q.lesson_id
            LEFT JOIN trails t ON t.id = q.trail_id
            WHERE q.id = :quiz_id AND q.is_active = 1
            """
        ),
        {"quiz_id": quiz_id},
    ).mappings().first()
    if not quiz:
        return None

    questions = db.execute(
        text(
            """
            SELECT id, position, prompt, explanation
            FROM quiz_questions
            WHERE quiz_id = :quiz_id
            ORDER BY position
            """
        ),
        {"quiz_id": quiz_id},
    ).mappings().all()

    items = []
    for question in questions:
        options = db.execute(
            text(
                """
                SELECT id, position, option_text
                FROM quiz_options
                WHERE question_id = :question_id
                ORDER BY position
                """
            ),
            {"question_id": question["id"]},
        ).mappings().all()
        items.append(
            {
                "id": int(question["id"]),
                "position": int(question["position"]),
                "prompt": str(question["prompt"]),
                "explanation": str(question["explanation"]),
                "options": [
                    {
                        "id": int(opt["id"]),
                        "position": int(opt["position"]),
                        "text": str(opt["option_text"]),
                    }
                    for opt in options
                ],
            }
        )

    return {
        "id": int(quiz["id"]),
        "slug": str(quiz["slug"]),
        "title": str(quiz["title"]),
        "passing_score": int(quiz["passing_score"]),
        "lesson_id": int(quiz["lesson_id"]) if quiz["lesson_id"] is not None else None,
        "trail_id": int(quiz["trail_id"]) if quiz["trail_id"] is not None else None,
        "lesson_title": str(quiz["lesson_title"]) if quiz["lesson_title"] else None,
        "trail_title": str(quiz["trail_title"]) if quiz["trail_title"] else None,
        "lesson_context": [
            str(card.get("text", ""))
            for card in json.loads(quiz["lesson_cards_json"] or "[]")
            if isinstance(card, dict) and card.get("text")
        ][:4],
        "questions": items,
    }


def _auto_complete_challenge_for_lesson(db: Session, user_pk: int, lesson_id: int) -> tuple[bool, int]:
    challenge = db.execute(
        text(
            """
            SELECT id, steps_json, xp_reward
            FROM challenges
            WHERE lesson_id = :lesson_id AND is_active = 1
            ORDER BY id
            LIMIT 1
            """
        ),
        {"lesson_id": lesson_id},
    ).mappings().first()
    if not challenge:
        return False, 0

    challenge_id = int(challenge["id"])
    existing = db.execute(
        text("SELECT id FROM challenge_completion WHERE user_pk = :user_pk AND challenge_id = :challenge_id"),
        {"user_pk": user_pk, "challenge_id": challenge_id},
    ).mappings().first()
    if existing:
        return False, 0

    steps = json.loads(challenge["steps_json"] or "[]")
    checklist = [{"step": str(step), "done": True} for step in steps]
    db.execute(
        text(
            """
            INSERT INTO challenge_completion (user_pk, challenge_id, status, checklist_json, completed_at, created_at)
            VALUES (:user_pk, :challenge_id, 'completed', :checklist_json, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """
        ),
        {
            "user_pk": user_pk,
            "challenge_id": challenge_id,
            "checklist_json": json.dumps(checklist),
        },
    )

    xp_reward = int(challenge["xp_reward"] or 0)
    if xp_reward > 0:
        db.execute(
            text(
                """
                INSERT INTO xp_events (user_pk, source_type, source_id, points, reason)
                VALUES (:user_pk, 'challenge', :source_id, :points, :reason)
                """
            ),
            {
                "user_pk": user_pk,
                "source_id": str(challenge_id),
                "points": xp_reward,
                "reason": "auto challenge completion by quiz pass",
            },
        )

    return True, xp_reward


def _is_trail_completed(db: Session, user_pk: int, trail_id: int) -> bool:
    total_lessons = int(
        db.execute(
            text("SELECT COUNT(*) FROM lessons WHERE trail_id = :trail_id AND is_active = 1"),
            {"trail_id": trail_id},
        ).scalar_one()
    )
    done_lessons = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM lesson_completion lc
                JOIN lessons l ON l.id = lc.lesson_id
                WHERE lc.user_pk = :user_pk
                  AND l.trail_id = :trail_id
                  AND l.is_active = 1
                """
            ),
            {"user_pk": user_pk, "trail_id": trail_id},
        ).scalar_one()
    )
    return total_lessons > 0 and done_lessons >= total_lessons


def _next_lesson_id(db: Session, user_pk: int, trail_id: int) -> int | None:
    row = db.execute(
        text(
            """
            SELECT l.id
            FROM lessons l
            WHERE l.trail_id = :trail_id
              AND l.is_active = 1
              AND NOT EXISTS (
                SELECT 1
                FROM lesson_completion lc
                WHERE lc.user_pk = :user_pk AND lc.lesson_id = l.id
              )
            ORDER BY l.position
            LIMIT 1
            """
        ),
        {"trail_id": trail_id, "user_pk": user_pk},
    ).mappings().first()
    return int(row["id"]) if row else None


def _refresh_generated_trails_for_user(db: Session, user_pk: int) -> None:
    completed_lessons = {
        int(row["lesson_id"])
        for row in db.execute(
            text("SELECT lesson_id FROM lesson_completion WHERE user_pk = :user_pk"),
            {"user_pk": user_pk},
        ).mappings().all()
    }
    generated_rows = db.execute(
        text(
            """
            SELECT id, lesson_bundle_json
            FROM generated_trails
            WHERE user_pk = :user_pk AND status = 'active'
            """
        ),
        {"user_pk": user_pk},
    ).mappings().all()
    for row in generated_rows:
        raw_bundle = json.loads(row["lesson_bundle_json"] or "[]")
        lesson_ids = []
        for value in raw_bundle:
            if isinstance(value, int):
                lesson_ids.append(value)
            elif isinstance(value, str) and value.isdigit():
                lesson_ids.append(int(value))
        if lesson_ids and all(lesson_id in completed_lessons for lesson_id in lesson_ids):
            db.execute(
                text("UPDATE generated_trails SET status = 'completed' WHERE id = :id"),
                {"id": int(row["id"])},
            )


def submit_quiz_attempt(db: Session, user_pk: int, quiz_id: int, answers: list[dict[str, int]]) -> dict[str, Any]:
    quiz = db.execute(
        text("SELECT id, passing_score, lesson_id, trail_id FROM quizzes WHERE id = :quiz_id AND is_active = 1"),
        {"quiz_id": quiz_id},
    ).mappings().first()
    if not quiz:
        raise ValueError("quiz not found")

    questions = db.execute(
        text(
            """
            SELECT qq.id AS question_id, qq.explanation, qo.id AS correct_option_id
            FROM quiz_questions qq
            JOIN quiz_options qo ON qo.question_id = qq.id AND qo.is_correct = 1
            WHERE qq.quiz_id = :quiz_id
            ORDER BY qq.position
            """
        ),
        {"quiz_id": quiz_id},
    ).mappings().all()
    if not questions:
        raise ValueError("quiz has no questions")

    answer_map = {int(item["question_id"]): int(item["option_id"]) for item in answers}
    total = len(questions)
    correct = 0
    feedback = []
    for q in questions:
        qid = int(q["question_id"])
        is_correct = answer_map.get(qid) == int(q["correct_option_id"])
        if is_correct:
            correct += 1
        else:
            feedback.append(
                {
                    "question_id": qid,
                    "is_correct": False,
                    "explanation": q["explanation"],
                }
            )

    score = int((correct / total) * 100)
    passed = score >= int(quiz["passing_score"])

    previous_stats = db.execute(
        text(
            """
            SELECT COUNT(*) AS attempts, MAX(score) AS best_score
            FROM quiz_attempts
            WHERE user_pk = :user_pk AND quiz_id = :quiz_id
            """
        ),
        {"user_pk": user_pk, "quiz_id": quiz_id},
    ).mappings().one()
    attempts_before = int(previous_stats["attempts"] or 0)
    previous_best_score = (
        int(previous_stats["best_score"]) if previous_stats["best_score"] is not None else None
    )

    xp_awarded = 0
    xp_reason = "sem ganho adicional de XP"
    if previous_best_score is None:
        xp_awarded = max(6, min(20, 8 + (score // 8)))
        xp_reason = "primeira tentativa no quiz"
    else:
        improvement = max(0, score - previous_best_score)
        xp_awarded = min(8, improvement // 10)
        if previous_best_score < int(quiz["passing_score"]) <= score:
            xp_awarded += 6
        if xp_awarded > 0:
            xp_reason = "melhora de desempenho no quiz"

    db.execute(
        text(
            """
            INSERT INTO quiz_attempts (user_pk, quiz_id, score, max_score, answers_json)
            VALUES (:user_pk, :quiz_id, :score, :max_score, :answers_json)
            """
        ),
        {
            "user_pk": user_pk,
            "quiz_id": quiz_id,
            "score": score,
            "max_score": 100,
            "answers_json": json.dumps(answers),
        },
    )
    if xp_awarded > 0:
        db.execute(
            text(
                """
                INSERT INTO xp_events (user_pk, source_type, source_id, points, reason)
                VALUES (:user_pk, 'quiz', :source_id, :points, :reason)
                """
            ),
            {
                "user_pk": user_pk,
                "source_id": str(quiz_id),
                "points": xp_awarded,
                "reason": xp_reason,
            },
        )

    lesson_completed = False
    lesson_xp_awarded = 0
    challenge_completed = False
    challenge_xp_awarded = 0
    trail_completed = False
    next_lesson_id = None
    completion_message = None

    if passed and quiz.get("lesson_id") is not None:
        lesson_completion = complete_lesson(db, user_pk=user_pk, lesson_id=int(quiz["lesson_id"]), seconds_spent=60)
        lesson_completed = lesson_completion["status"] == "completed"
        lesson_xp_awarded = int(lesson_completion["xp_awarded"])

        challenge_completed, challenge_xp_awarded = _auto_complete_challenge_for_lesson(db, user_pk=user_pk, lesson_id=int(quiz["lesson_id"]))
        if quiz.get("trail_id") is not None:
            trail_completed = _is_trail_completed(db, user_pk=user_pk, trail_id=int(quiz["trail_id"]))
            next_lesson_id = _next_lesson_id(db, user_pk=user_pk, trail_id=int(quiz["trail_id"]))

        _refresh_generated_trails_for_user(db, user_pk=user_pk)
        completion_message = "trilha ou desafio concluido"

    db.commit()

    return {
        "score": score,
        "max_score": 100,
        "passed": passed,
        "feedback": feedback,
        "xp_awarded": xp_awarded,
        "xp_reason": xp_reason,
        "attempt_number": attempts_before + 1,
        "best_score": max(score, previous_best_score or 0),
        "xp_locked": xp_awarded == 0,
        "lesson_completed": lesson_completed,
        "lesson_xp_awarded": lesson_xp_awarded,
        "challenge_completed": challenge_completed,
        "challenge_xp_awarded": challenge_xp_awarded,
        "trail_completed": trail_completed,
        "next_lesson_id": next_lesson_id,
        "completion_message": completion_message,
    }
