from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, validate_payload
from app.db.session import get_db
from app.schemas.contracts import QuizAttemptIn, UserCtx
from app.services import content_service

router = APIRouter(tags=["content"])


@router.get("/challenges")
def get_challenges(
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": content_service.list_user_challenges(db, user.pk)}


@router.get("/trails")
def get_trails(
    age_group: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    items = content_service.list_trails(db, age_group)
    return {"items": items}


@router.get("/lessons/{lesson_id}")
def get_lesson(lesson_id: int, db: Session = Depends(get_db)):
    lesson = content_service.get_lesson(db, lesson_id)
    if not lesson:
        raise HTTPException(status_code=404, detail="lesson not found")
    return lesson


@router.post("/lessons/{lesson_id}/complete")
def complete_lesson(
    lesson_id: int,
    payload: dict = Body(default={}),
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    seconds_spent = int(payload.get("seconds_spent", 0))
    try:
        return content_service.complete_lesson(db, user_pk=user.pk, lesson_id=lesson_id, seconds_spent=seconds_spent)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/quizzes/{quiz_id}")
def get_quiz(quiz_id: int, db: Session = Depends(get_db)):
    quiz = content_service.get_quiz(db, quiz_id)
    if not quiz:
        raise HTTPException(status_code=404, detail="quiz not found")
    return quiz


@router.post("/quizzes/{quiz_id}/attempt")
def submit_quiz(
    quiz_id: int,
    payload: dict = Body(...),
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_payload("content", "quiz_attempt", payload)
    data = QuizAttemptIn.model_validate(payload)
    try:
        result = content_service.submit_quiz_attempt(
            db, user_pk=user.pk, quiz_id=quiz_id, answers=[item.model_dump() for item in data.answers]
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return result
