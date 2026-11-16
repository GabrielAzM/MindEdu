from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import enforce_rate_limit, get_request_ip, validate_payload
from app.core.audit import write_audit
from app.db.session import get_db
from app.schemas.contracts import LoginIn, RefreshIn, RegisterIn
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register")
def register(
    payload: dict = Body(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    validate_payload("auth", "register", payload)
    data = RegisterIn.model_validate(payload)

    enforce_rate_limit(
        db,
        action_key="register",
        max_hits=5,
        window_seconds=3600,
        user_pk=None,
        ip_address=get_request_ip(request),
    )

    try:
        user = auth_service.register_user(db, data.email, data.username, data.password)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    write_audit(
        db,
        actor_user_pk=user["id"],
        actor_role=user["role"],
        action="auth.register",
        entity_type="user",
        entity_id=user["user_id"],
        payload={"email": data.email, "username": data.username},
        request=request,
    )

    return {
        "user_id": user["user_id"],
        "message": f"Sua conta foi criada com sucesso. Seu ID é {user['user_id']}. Aguarde a aprovação do seu cadastro.",
    }


@router.post("/login")
def login(
    payload: dict = Body(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    validate_payload("auth", "login", payload)
    data = LoginIn.model_validate(payload)

    enforce_rate_limit(
        db,
        action_key="login",
        max_hits=10,
        window_seconds=900,
        user_pk=None,
        ip_address=get_request_ip(request),
    )

    try:
        user = auth_service.authenticate(db, data.user_id, data.password)
        tokens = auth_service.issue_tokens(db, user)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    write_audit(
        db,
        actor_user_pk=user["id"],
        actor_role=user["role"],
        action="auth.login",
        entity_type="user",
        entity_id=user["user_id"],
        payload={},
        request=request,
    )

    return tokens


@router.post("/refresh")
def refresh(
    payload: dict = Body(...),
    request: Request = None,
    db: Session = Depends(get_db),
):
    validate_payload("auth", "refresh", payload)
    data = RefreshIn.model_validate(payload)
    try:
        tokens = auth_service.refresh(db, data.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    write_audit(
        db,
        actor_user_pk=None,
        actor_role="user",
        action="auth.refresh",
        entity_type="token",
        entity_id=None,
        payload={},
        request=request,
    )
    return {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "token_type": tokens["token_type"],
        "expires_in": tokens["expires_in"],
    }
