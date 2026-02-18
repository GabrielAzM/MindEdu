from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import require_admin, validate_payload
from app.core.audit import write_audit
from app.db.session import get_db
from app.schemas.contracts import (
    AdminQuizOptionCreateIn,
    AdminQuizOptionUpdateIn,
    AdminQuizQuestionCreateIn,
    AdminQuizQuestionUpdateIn,
    AdminUserActionIn,
    ReportResolveIn,
    UserCtx,
)
from app.services import moderation_service

router = APIRouter(prefix="/admin", tags=["admin"])


def _update_row(
    db: Session,
    table: str,
    row_id: int,
    payload: dict[str, Any],
    allowed_fields: set[str],
) -> None:
    updates = {k: v for k, v in payload.items() if k in allowed_fields}
    if not updates:
        raise ValueError("no valid fields to update")

    if "cards" in updates:
        updates["cards_json"] = json.dumps(updates.pop("cards"))
    if "steps" in updates:
        updates["steps_json"] = json.dumps(updates.pop("steps"))
    if "safety_notes" in updates:
        updates["safety_notes_json"] = json.dumps(updates.pop("safety_notes"))

    set_clause = ", ".join([f"{field} = :{field}" for field in updates])
    updates["id"] = row_id
    db.execute(text(f"UPDATE {table} SET {set_clause} WHERE id = :id"), updates)
    db.commit()


def _question_summary(db: Session, quiz_id: int) -> list[dict[str, Any]]:
    question_rows = db.execute(
        text(
            """
            SELECT id, quiz_id, position, prompt, explanation
            FROM quiz_questions
            WHERE quiz_id = :quiz_id
            ORDER BY position, id
            """
        ),
        {"quiz_id": quiz_id},
    ).mappings().all()
    if not question_rows:
        return []

    question_ids = [int(row["id"]) for row in question_rows]
    placeholders = ",".join([str(qid) for qid in question_ids])
    option_rows = db.execute(
        text(
            f"""
            SELECT id, question_id, position, option_text, is_correct
            FROM quiz_options
            WHERE question_id IN ({placeholders})
            ORDER BY question_id, position, id
            """
        )
    ).mappings().all()

    by_question: dict[int, list[dict[str, Any]]] = {qid: [] for qid in question_ids}
    for row in option_rows:
        option = dict(row)
        option["is_correct"] = bool(option["is_correct"])
        by_question[int(option["question_id"])].append(option)

    result: list[dict[str, Any]] = []
    for row in question_rows:
        question = dict(row)
        question["options"] = by_question.get(int(question["id"]), [])
        result.append(question)
    return result


@router.get("/trails")
def admin_list_trails(
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.execute(text("SELECT * FROM trails ORDER BY id DESC")).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.post("/trails")
def admin_create_trail(
    payload: dict = Body(...),
    request: Request = None,
    admin: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    required = {"slug", "title", "description", "age_group"}
    if not required.issubset(set(payload.keys())):
        raise HTTPException(status_code=422, detail="missing required fields")

    row = db.execute(
        text(
            """
            INSERT INTO trails (slug, title, description, age_group, is_active, created_by)
            VALUES (:slug, :title, :description, :age_group, :is_active, :created_by)
            RETURNING id
            """
        ),
        {
            "slug": payload["slug"],
            "title": payload["title"],
            "description": payload["description"],
            "age_group": payload["age_group"],
            "is_active": 1 if payload.get("is_active", True) else 0,
            "created_by": admin.pk,
        },
    ).mappings().one()
    db.commit()

    write_audit(
        db,
        actor_user_pk=admin.pk,
        actor_role=admin.role,
        action="admin.trails.create",
        entity_type="trail",
        entity_id=str(row["id"]),
        payload=payload,
        request=request,
    )
    return {"id": int(row["id"])}


@router.patch("/trails/{trail_id}")
def admin_update_trail(
    trail_id: int,
    payload: dict = Body(...),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        _update_row(db, "trails", trail_id, payload, {"slug", "title", "description", "age_group", "is_active"})
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok"}


@router.delete("/trails/{trail_id}")
def admin_delete_trail(
    trail_id: int,
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    db.execute(text("DELETE FROM trails WHERE id = :id"), {"id": trail_id})
    db.commit()
    return {"status": "ok"}


@router.get("/lessons")
def admin_list_lessons(_: UserCtx = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM lessons ORDER BY trail_id, position")).mappings().all()
    items = []
    for row in rows:
        item = dict(row)
        item["cards"] = json.loads(item.pop("cards_json"))
        items.append(item)
    return {"items": items}


@router.post("/lessons")
def admin_create_lesson(
    payload: dict = Body(...),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    required = {"trail_id", "slug", "title", "position", "duration_min", "cards"}
    if not required.issubset(payload.keys()):
        raise HTTPException(status_code=422, detail="missing required fields")

    row = db.execute(
        text(
            """
            INSERT INTO lessons (trail_id, slug, title, position, duration_min, cards_json, is_active)
            VALUES (:trail_id, :slug, :title, :position, :duration_min, :cards_json, :is_active)
            RETURNING id
            """
        ),
        {
            "trail_id": payload["trail_id"],
            "slug": payload["slug"],
            "title": payload["title"],
            "position": payload["position"],
            "duration_min": payload["duration_min"],
            "cards_json": json.dumps(payload["cards"]),
            "is_active": 1 if payload.get("is_active", True) else 0,
        },
    ).mappings().one()
    db.commit()
    return {"id": int(row["id"])}


@router.patch("/lessons/{lesson_id}")
def admin_update_lesson(
    lesson_id: int,
    payload: dict = Body(...),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        _update_row(
            db,
            "lessons",
            lesson_id,
            payload,
            {"trail_id", "slug", "title", "position", "duration_min", "cards", "is_active"},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok"}


@router.delete("/lessons/{lesson_id}")
def admin_delete_lesson(
    lesson_id: int,
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    db.execute(text("DELETE FROM lessons WHERE id = :id"), {"id": lesson_id})
    db.commit()
    return {"status": "ok"}


@router.get("/quizzes")
def admin_list_quizzes(_: UserCtx = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM quizzes ORDER BY id DESC")).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.post("/quizzes")
def admin_create_quiz(
    payload: dict = Body(...),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    required = {"trail_id", "slug", "title"}
    if not required.issubset(payload.keys()):
        raise HTTPException(status_code=422, detail="missing required fields")

    row = db.execute(
        text(
            """
            INSERT INTO quizzes (trail_id, lesson_id, slug, title, passing_score, is_active)
            VALUES (:trail_id, :lesson_id, :slug, :title, :passing_score, :is_active)
            RETURNING id
            """
        ),
        {
            "trail_id": payload["trail_id"],
            "lesson_id": payload.get("lesson_id"),
            "slug": payload["slug"],
            "title": payload["title"],
            "passing_score": payload.get("passing_score", 70),
            "is_active": 1 if payload.get("is_active", True) else 0,
        },
    ).mappings().one()
    db.commit()
    return {"id": int(row["id"])}


@router.patch("/quizzes/{quiz_id}")
def admin_update_quiz(
    quiz_id: int,
    payload: dict = Body(...),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        _update_row(
            db,
            "quizzes",
            quiz_id,
            payload,
            {"trail_id", "lesson_id", "slug", "title", "passing_score", "is_active"},
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok"}


@router.delete("/quizzes/{quiz_id}")
def admin_delete_quiz(
    quiz_id: int,
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    db.execute(text("DELETE FROM quizzes WHERE id = :id"), {"id": quiz_id})
    db.commit()
    return {"status": "ok"}


@router.get("/quizzes/{quiz_id}/questions")
def admin_list_quiz_questions(
    quiz_id: int,
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    quiz = db.execute(text("SELECT id FROM quizzes WHERE id = :id"), {"id": quiz_id}).mappings().first()
    if not quiz:
        raise HTTPException(status_code=404, detail="quiz not found")
    return {"items": _question_summary(db, quiz_id)}


@router.post("/quizzes/{quiz_id}/questions")
def admin_create_quiz_question(
    quiz_id: int,
    payload: dict = Body(...),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    data = AdminQuizQuestionCreateIn.model_validate(payload)
    if not any(option.is_correct for option in data.options):
        raise HTTPException(status_code=422, detail="at least one option must be correct")

    quiz = db.execute(text("SELECT id FROM quizzes WHERE id = :id"), {"id": quiz_id}).mappings().first()
    if not quiz:
        raise HTTPException(status_code=404, detail="quiz not found")

    try:
        question = db.execute(
            text(
                """
                INSERT INTO quiz_questions (quiz_id, position, prompt, explanation)
                VALUES (:quiz_id, :position, :prompt, :explanation)
                RETURNING id
                """
            ),
            {
                "quiz_id": quiz_id,
                "position": data.position,
                "prompt": data.prompt,
                "explanation": data.explanation,
            },
        ).mappings().one()

        question_id = int(question["id"])
        for option in data.options:
            db.execute(
                text(
                    """
                    INSERT INTO quiz_options (question_id, position, option_text, is_correct)
                    VALUES (:question_id, :position, :option_text, :is_correct)
                    """
                ),
                {
                    "question_id": question_id,
                    "position": option.position,
                    "option_text": option.option_text,
                    "is_correct": 1 if option.is_correct else 0,
                },
            )
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="duplicate question/option position") from exc

    return {"id": question_id}


@router.patch("/quiz-questions/{question_id}")
def admin_update_quiz_question(
    question_id: int,
    payload: dict = Body(...),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    data = AdminQuizQuestionUpdateIn.model_validate(payload)
    updates = data.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="no fields to update")

    exists = db.execute(text("SELECT id FROM quiz_questions WHERE id = :id"), {"id": question_id}).mappings().first()
    if not exists:
        raise HTTPException(status_code=404, detail="question not found")

    set_clause = ", ".join([f"{key} = :{key}" for key in updates.keys()])
    updates["id"] = question_id
    try:
        db.execute(text(f"UPDATE quiz_questions SET {set_clause} WHERE id = :id"), updates)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="duplicate question position") from exc
    return {"status": "ok"}


@router.delete("/quiz-questions/{question_id}")
def admin_delete_quiz_question(
    question_id: int,
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    exists = db.execute(text("SELECT id FROM quiz_questions WHERE id = :id"), {"id": question_id}).mappings().first()
    if not exists:
        raise HTTPException(status_code=404, detail="question not found")
    db.execute(text("DELETE FROM quiz_questions WHERE id = :id"), {"id": question_id})
    db.commit()
    return {"status": "ok"}


@router.post("/quiz-questions/{question_id}/options")
def admin_create_quiz_option(
    question_id: int,
    payload: dict = Body(...),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    data = AdminQuizOptionCreateIn.model_validate(payload)
    question = db.execute(
        text("SELECT id FROM quiz_questions WHERE id = :id"),
        {"id": question_id},
    ).mappings().first()
    if not question:
        raise HTTPException(status_code=404, detail="question not found")

    try:
        row = db.execute(
            text(
                """
                INSERT INTO quiz_options (question_id, position, option_text, is_correct)
                VALUES (:question_id, :position, :option_text, :is_correct)
                RETURNING id
                """
            ),
            {
                "question_id": question_id,
                "position": data.position,
                "option_text": data.option_text,
                "is_correct": 1 if data.is_correct else 0,
            },
        ).mappings().one()
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="duplicate option position") from exc

    return {"id": int(row["id"])}


@router.patch("/quiz-options/{option_id}")
def admin_update_quiz_option(
    option_id: int,
    payload: dict = Body(...),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    data = AdminQuizOptionUpdateIn.model_validate(payload)
    updates = data.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="no fields to update")

    row = db.execute(
        text("SELECT id, question_id FROM quiz_options WHERE id = :id"),
        {"id": option_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="option not found")

    set_clause = ", ".join([f"{key} = :{key}" for key in updates.keys()])
    updates["id"] = option_id
    if "is_correct" in updates:
        updates["is_correct"] = 1 if bool(updates["is_correct"]) else 0

    try:
        db.execute(text(f"UPDATE quiz_options SET {set_clause} WHERE id = :id"), updates)
        if "is_correct" in updates and updates["is_correct"] == 0:
            has_correct = db.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM quiz_options
                    WHERE question_id = :question_id AND is_correct = 1
                    """
                ),
                {"question_id": row["question_id"]},
            ).scalar_one()
            if int(has_correct) == 0:
                db.rollback()
                raise HTTPException(status_code=422, detail="question must keep at least one correct option")
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="duplicate option position") from exc

    return {"status": "ok"}


@router.delete("/quiz-options/{option_id}")
def admin_delete_quiz_option(
    option_id: int,
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    row = db.execute(
        text("SELECT id, question_id, is_correct FROM quiz_options WHERE id = :id"),
        {"id": option_id},
    ).mappings().first()
    if not row:
        raise HTTPException(status_code=404, detail="option not found")

    count_options = db.execute(
        text("SELECT COUNT(*) FROM quiz_options WHERE question_id = :question_id"),
        {"question_id": row["question_id"]},
    ).scalar_one()
    if int(count_options) <= 2:
        raise HTTPException(status_code=422, detail="question must have at least two options")

    if int(row["is_correct"]) == 1:
        count_correct = db.execute(
            text("SELECT COUNT(*) FROM quiz_options WHERE question_id = :question_id AND is_correct = 1"),
            {"question_id": row["question_id"]},
        ).scalar_one()
        if int(count_correct) <= 1:
            raise HTTPException(status_code=422, detail="question must keep at least one correct option")

    db.execute(text("DELETE FROM quiz_options WHERE id = :id"), {"id": option_id})
    db.commit()
    return {"status": "ok"}


@router.get("/challenges")
def admin_list_challenges(_: UserCtx = Depends(require_admin), db: Session = Depends(get_db)):
    rows = db.execute(text("SELECT * FROM challenges ORDER BY id DESC")).mappings().all()
    items = []
    for row in rows:
        item = dict(row)
        item["steps"] = json.loads(item.pop("steps_json"))
        item["safety_notes"] = json.loads(item.pop("safety_notes_json"))
        items.append(item)
    return {"items": items}


@router.post("/challenges")
def admin_create_challenge(
    payload: dict = Body(...),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    required = {"trail_id", "slug", "title", "steps", "safety_notes"}
    if not required.issubset(payload.keys()):
        raise HTTPException(status_code=422, detail="missing required fields")

    row = db.execute(
        text(
            """
            INSERT INTO challenges (trail_id, lesson_id, slug, title, steps_json, safety_notes_json, xp_reward, is_active)
            VALUES (:trail_id, :lesson_id, :slug, :title, :steps_json, :safety_notes_json, :xp_reward, :is_active)
            RETURNING id
            """
        ),
        {
            "trail_id": payload["trail_id"],
            "lesson_id": payload.get("lesson_id"),
            "slug": payload["slug"],
            "title": payload["title"],
            "steps_json": json.dumps(payload["steps"]),
            "safety_notes_json": json.dumps(payload["safety_notes"]),
            "xp_reward": payload.get("xp_reward", 20),
            "is_active": 1 if payload.get("is_active", True) else 0,
        },
    ).mappings().one()
    db.commit()
    return {"id": int(row["id"])}


@router.patch("/challenges/{challenge_id}")
def admin_update_challenge(
    challenge_id: int,
    payload: dict = Body(...),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    try:
        _update_row(
            db,
            "challenges",
            challenge_id,
            payload,
            {
                "trail_id",
                "lesson_id",
                "slug",
                "title",
                "steps",
                "safety_notes",
                "xp_reward",
                "is_active",
            },
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"status": "ok"}


@router.delete("/challenges/{challenge_id}")
def admin_delete_challenge(
    challenge_id: int,
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    db.execute(text("DELETE FROM challenges WHERE id = :id"), {"id": challenge_id})
    db.commit()
    return {"status": "ok"}


@router.get("/moderation/reports")
def admin_reports(
    status: str | None = Query(default=None),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return {"items": moderation_service.list_reports(db, status=status)}


@router.post("/moderation/reports/{report_id}/resolve")
def admin_resolve_report(
    report_id: int,
    payload: dict = Body(...),
    request: Request = None,
    admin: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    validate_payload("admin", "report_resolve", payload)
    data = ReportResolveIn.model_validate(payload)
    try:
        result = moderation_service.resolve_report(
            db,
            report_id=report_id,
            admin_user_pk=admin.pk,
            resolution=data.resolution,
            note=data.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    audit_id = write_audit(
        db,
        actor_user_pk=admin.pk,
        actor_role=admin.role,
        action="admin.report.resolve",
        entity_type="report",
        entity_id=str(report_id),
        payload=payload,
        request=request,
    )
    result["audit_id"] = audit_id
    return result


@router.post("/users/{target_user_id}/action")
def admin_user_action(
    target_user_id: str,
    payload: dict = Body(...),
    request: Request = None,
    admin: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    validate_payload("admin", "user_action", payload)
    data = AdminUserActionIn.model_validate(payload)

    try:
        result = moderation_service.admin_user_action(
            db,
            admin_user_pk=admin.pk,
            target_user_id=target_user_id,
            action=data.action,
            reason=data.reason,
            duration_minutes=data.duration_minutes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_id = write_audit(
        db,
        actor_user_pk=admin.pk,
        actor_role=admin.role,
        action="admin.user.action",
        entity_type="user",
        entity_id=target_user_id,
        payload=payload,
        request=request,
    )

    return {
        "status": "ok",
        "audit_id": audit_id,
        **result,
    }


@router.delete("/users/{target_user_id}")
def admin_delete_user(
    target_user_id: str,
    payload: dict = Body(...),
    request: Request = None,
    admin: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    reason = str(payload.get("reason", "")).strip()
    if len(reason) < 3:
        raise HTTPException(status_code=422, detail="reason required")

    try:
        result = moderation_service.admin_delete_user(
            db,
            admin_user_pk=admin.pk,
            target_user_id=target_user_id,
            reason=reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audit_id = write_audit(
        db,
        actor_user_pk=admin.pk,
        actor_role=admin.role,
        action="admin.user.delete",
        entity_type="user",
        entity_id=target_user_id,
        payload={"reason": reason},
        request=request,
    )
    return {
        "status": "ok",
        "audit_id": audit_id,
        **result,
    }


@router.get("/users/approvals")
def admin_user_approvals(
    status: str = Query(default="pending"),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    if status not in {"pending", "approved", "rejected", "all"}:
        raise HTTPException(status_code=400, detail="invalid status")

    query = """
      SELECT id, user_id, email, username, status AS account_status, approval_status, created_at, approved_at, rejected_reason
      FROM users
      WHERE role = 'user'
    """
    params: dict[str, Any] = {}
    if status != "all":
        query += " AND approval_status = :approval_status"
        params["approval_status"] = status
    query += " ORDER BY created_at DESC"
    rows = db.execute(text(query), params).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.post("/users/{target_user_id}/approve")
def admin_approve_user(
    target_user_id: str,
    request: Request = None,
    admin: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    user = db.execute(
        text("SELECT id, approval_status FROM users WHERE user_id = :user_id AND role = 'user'"),
        {"user_id": target_user_id},
    ).mappings().first()
    if not user:
        raise HTTPException(status_code=404, detail="target user not found")

    if user["approval_status"] == "approved":
        return {"status": "ok", "message": "user already approved"}

    db.execute(
        text(
            """
            UPDATE users
            SET approval_status = 'approved',
                approved_by_user_pk = :admin_pk,
                approved_at = :approved_at,
                rejected_reason = NULL
            WHERE id = :id
            """
        ),
        {
            "id": user["id"],
            "admin_pk": admin.pk,
            "approved_at": datetime.now(UTC).isoformat(),
        },
    )
    db.commit()

    audit_id = write_audit(
        db,
        actor_user_pk=admin.pk,
        actor_role=admin.role,
        action="admin.user.approve_signup",
        entity_type="user",
        entity_id=target_user_id,
        payload={},
        request=request,
    )
    return {"status": "ok", "audit_id": audit_id}


@router.post("/users/{target_user_id}/reject")
def admin_reject_user(
    target_user_id: str,
    payload: dict = Body(...),
    request: Request = None,
    admin: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    reason = str(payload.get("reason", "")).strip()
    if len(reason) < 3:
        raise HTTPException(status_code=422, detail="reason required")

    user = db.execute(
        text("SELECT id, approval_status FROM users WHERE user_id = :user_id AND role = 'user'"),
        {"user_id": target_user_id},
    ).mappings().first()
    if not user:
        raise HTTPException(status_code=404, detail="target user not found")

    db.execute(
        text(
            """
            UPDATE users
            SET approval_status = 'rejected',
                approved_by_user_pk = :admin_pk,
                approved_at = NULL,
                rejected_reason = :reason
            WHERE id = :id
            """
        ),
        {
            "id": user["id"],
            "admin_pk": admin.pk,
            "reason": reason,
        },
    )
    db.commit()

    audit_id = write_audit(
        db,
        actor_user_pk=admin.pk,
        actor_role=admin.role,
        action="admin.user.reject_signup",
        entity_type="user",
        entity_id=target_user_id,
        payload={"reason": reason},
        request=request,
    )
    return {"status": "ok", "audit_id": audit_id}


@router.get("/audit")
def admin_audit(
    limit: int = Query(default=100, ge=1, le=500),
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        text(
            """
            SELECT id, actor_user_pk, actor_role, action, entity_type, entity_id, payload_json, created_at
            FROM audit_log
            ORDER BY created_at DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).mappings().all()
    return {"items": [dict(r) for r in rows]}


@router.get("/metrics")
def admin_metrics(
    _: UserCtx = Depends(require_admin),
    db: Session = Depends(get_db),
):
    users_total = int(db.execute(text("SELECT COUNT(*) FROM users WHERE role='user' ")).scalar_one())
    active_7d = int(
        db.execute(
            text("SELECT COUNT(DISTINCT user_pk) FROM api_usage_events WHERE created_at >= datetime('now','-7 days')")
        ).scalar_one()
    )
    reports_open = int(db.execute(text("SELECT COUNT(*) FROM reports WHERE status='open' ")).scalar_one())
    useful_feedback = int(db.execute(text("SELECT COUNT(*) FROM mission_feedback WHERE is_useful = 1")).scalar_one())
    approvals_pending = int(
        db.execute(text("SELECT COUNT(*) FROM users WHERE role='user' AND approval_status='pending'")).scalar_one()
    )

    return {
        "users_total": users_total,
        "active_7d": active_7d,
        "reports_open": reports_open,
        "useful_feedback": useful_feedback,
        "approvals_pending": approvals_pending,
    }
