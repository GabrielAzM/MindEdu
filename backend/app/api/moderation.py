from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import enforce_rate_limit, get_request_ip, require_not_muted, validate_payload
from app.core.audit import write_audit
from app.db.session import get_db
from app.schemas.contracts import ReportIn, UserCtx
from app.services import moderation_service

router = APIRouter(tags=["moderation"])


@router.post("/reports")
def create_report(
    payload: dict = Body(...),
    request: Request = None,
    user: UserCtx = Depends(require_not_muted),
    db: Session = Depends(get_db),
):
    validate_payload("moderation", "report_create", payload)
    data = ReportIn.model_validate(payload)

    enforce_rate_limit(
        db,
        action_key="reports:create",
        max_hits=20,
        window_seconds=24 * 3600,
        user_pk=user.pk,
        ip_address=get_request_ip(request),
    )

    result = moderation_service.create_report(
        db,
        reporter_user_pk=user.pk,
        target_type=data.target_type,
        target_id=data.target_id,
        reason=data.reason,
        details=data.details,
    )

    write_audit(
        db,
        actor_user_pk=user.pk,
        actor_role=user.role,
        action="report.create",
        entity_type=data.target_type,
        entity_id=data.target_id,
        payload={"reason": data.reason},
        request=request,
    )
    return result


@router.post("/block/{blocked_user_id}")
def block_user(
    blocked_user_id: str,
    request: Request = None,
    user: UserCtx = Depends(require_not_muted),
    db: Session = Depends(get_db),
):
    try:
        result = moderation_service.block_user(db, user.pk, blocked_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    write_audit(
        db,
        actor_user_pk=user.pk,
        actor_role=user.role,
        action="user.block",
        entity_type="user",
        entity_id=blocked_user_id,
        payload={},
        request=request,
    )
    return result
