from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.api.deps import enforce_rate_limit, get_current_user, get_request_ip, validate_payload
from app.db.session import get_db
from app.schemas.contracts import CheckinIn, UserCtx
from app.services import checkin_service

router = APIRouter(tags=["emotions"])


@router.post("/checkins")
def create_checkin(
    payload: dict = Body(...),
    request: Request = None,
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_payload("emotions", "checkin_create", payload)
    data = CheckinIn.model_validate(payload)

    enforce_rate_limit(
        db,
        action_key="checkins:create",
        max_hits=12,
        window_seconds=24 * 3600,
        user_pk=user.pk,
        ip_address=get_request_ip(request),
    )

    result = checkin_service.create_checkin(
        db,
        user_pk=user.pk,
        emotion=data.emotion,
        intensity=data.intensity,
        context_tags=data.context_tags,
        need_tags=list(data.need_tags),
    )
    return result


@router.get("/checkins")
def get_checkins(
    range: str = Query(default="week", pattern="^(week|month)$"),
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return checkin_service.list_checkins(db, user.pk, range)


@router.get("/insights")
def get_insights(
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return checkin_service.build_insights(db, user.pk)
