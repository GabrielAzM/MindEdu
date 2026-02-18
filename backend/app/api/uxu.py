from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import enforce_rate_limit, get_current_user, get_request_ip, require_not_muted, validate_payload
from app.db.session import get_db
from app.schemas.contracts import MissionCreateIn, MissionFeedbackIn, MissionRespondIn, UserCtx
from app.services import coop_service, mission_service

router = APIRouter(prefix="/missions", tags=["uxu"])
coop_router = APIRouter(prefix="/coop", tags=["coop"])


@router.post("")
def create_mission(
    payload: dict = Body(...),
    request: Request = None,
    user: UserCtx = Depends(require_not_muted),
    db: Session = Depends(get_db),
):
    validate_payload("uxu", "mission_create", payload)
    data = MissionCreateIn.model_validate(payload)

    enforce_rate_limit(
        db,
        action_key="missions:create",
        max_hits=5,
        window_seconds=24 * 3600,
        user_pk=user.pk,
        ip_address=get_request_ip(request),
    )

    try:
        return mission_service.create_mission(
            db,
            creator_user_pk=user.pk,
            category=data.category,
            intensity=data.intensity,
            context_tags=data.context_tags,
            want_now=data.want_now,
            partner_user_id=data.partner_user_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/inbox")
def missions_inbox(
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": mission_service.inbox(db, user.pk)}


@router.get("/support-cards")
def list_support_cards(
    category: str = Query(...),
    tone: str = Query(...),
    _: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": mission_service.list_support_cards(db, category=category, tone=tone)}


@router.get("/{mission_id}")
def mission_details(
    mission_id: int,
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        mission = mission_service.get_mission(db, mission_id, viewer_user_pk=user.pk)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    if not mission:
        raise HTTPException(status_code=404, detail="mission not found")
    return mission


@router.post("/{mission_id}/respond")
def respond_mission(
    mission_id: int,
    payload: dict = Body(...),
    request: Request = None,
    user: UserCtx = Depends(require_not_muted),
    db: Session = Depends(get_db),
):
    validate_payload("uxu", "mission_respond", payload)
    data = MissionRespondIn.model_validate(payload)

    enforce_rate_limit(
        db,
        action_key="missions:respond",
        max_hits=30,
        window_seconds=24 * 3600,
        user_pk=user.pk,
        ip_address=get_request_ip(request),
    )

    try:
        return mission_service.respond(
            db,
            mission_id=mission_id,
            responder_user_pk=user.pk,
            card_id=data.card_id,
            guided_actions_selected=data.guided_actions_selected,
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="resposta ja registrada para esta missao") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{mission_id}/feedback")
def mission_feedback(
    mission_id: int,
    payload: dict = Body(...),
    user: UserCtx = Depends(require_not_muted),
    db: Session = Depends(get_db),
):
    validate_payload("uxu", "mission_feedback", payload)
    data = MissionFeedbackIn.model_validate(payload)
    try:
        return mission_service.feedback(
            db,
            mission_id=mission_id,
            from_user_pk=user.pk,
            response_id=data.response_id,
            useful=data.useful,
            best_response=data.best_response,
        )
    except IntegrityError as exc:
        raise HTTPException(status_code=409, detail="feedback ja registrado") from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@coop_router.post("/pairs")
def create_coop_pair(
    payload: dict = Body(...),
    request: Request = None,
    user: UserCtx = Depends(require_not_muted),
    db: Session = Depends(get_db),
):
    partner_user_id = str(payload.get("partner_user_id", "")).strip()
    if len(partner_user_id) < 6:
        raise HTTPException(status_code=422, detail="partner_user_id required")

    enforce_rate_limit(
        db,
        action_key="coop:pairs:create",
        max_hits=10,
        window_seconds=24 * 3600,
        user_pk=user.pk,
        ip_address=get_request_ip(request),
    )

    try:
        return coop_service.create_pair_request(db, requester_user_pk=user.pk, partner_user_id=partner_user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@coop_router.get("/pairs")
def list_coop_pairs(
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": coop_service.list_pairs(db, user.pk)}


@coop_router.post("/pairs/{pair_id}/confirm")
def confirm_coop_pair(
    pair_id: int,
    payload: dict = Body(...),
    user: UserCtx = Depends(require_not_muted),
    db: Session = Depends(get_db),
):
    accept = bool(payload.get("accept", True))
    try:
        return coop_service.confirm_pair(db, pair_id=pair_id, actor_user_pk=user.pk, accept=accept)
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
