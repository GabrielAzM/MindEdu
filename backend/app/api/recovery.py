from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import enforce_rate_limit, get_request_ip, validate_payload
from app.core.audit import write_audit
from app.db.session import get_db
from app.schemas.contracts import ForgotIn, RecoveryConfirmIn
from app.services import recovery_service

router = APIRouter(prefix="/recovery", tags=["recovery"])


@router.post("/forgot-id")
def forgot_id(
    payload: dict = Body(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    validate_payload("recovery", "forgot_id", payload)
    data = ForgotIn.model_validate(payload)

    enforce_rate_limit(
        db,
        action_key="recovery.forgot_id",
        max_hits=5,
        window_seconds=3600,
        user_pk=None,
        ip_address=get_request_ip(request),
    )

    request_id = recovery_service.create_recovery_request(db, data.email, "forgot_id")
    write_audit(
        db,
        actor_user_pk=None,
        actor_role="guest",
        action="recovery.forgot_id",
        entity_type="account_request",
        entity_id=request_id,
        payload={"email": data.email},
        request=request,
    )

    return {
        "request_id": request_id,
        "message": "Se o email existir, enviamos um codigo de confirmacao.",
    }


@router.post("/reset-password")
def reset_password(
    payload: dict = Body(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    validate_payload("recovery", "reset_password", payload)
    data = ForgotIn.model_validate(payload)

    enforce_rate_limit(
        db,
        action_key="recovery.reset_password",
        max_hits=5,
        window_seconds=3600,
        user_pk=None,
        ip_address=get_request_ip(request),
    )

    request_id = recovery_service.create_recovery_request(db, data.email, "reset_password")
    write_audit(
        db,
        actor_user_pk=None,
        actor_role="guest",
        action="recovery.reset_password",
        entity_type="account_request",
        entity_id=request_id,
        payload={"email": data.email},
        request=request,
    )

    return {
        "request_id": request_id,
        "message": "Se o email existir, enviamos um codigo de confirmacao.",
    }


@router.post("/confirm")
def confirm_recovery(
    payload: dict = Body(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    validate_payload("recovery", "confirm", payload)
    data = RecoveryConfirmIn.model_validate(payload)

    try:
        result = recovery_service.confirm_recovery(db, data.request_id, data.token, data.new_password)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    write_audit(
        db,
        actor_user_pk=None,
        actor_role="guest",
        action="recovery.confirm",
        entity_type="account_request",
        entity_id=data.request_id,
        payload={"result_keys": list(result.keys())},
        request=request,
    )
    return result
