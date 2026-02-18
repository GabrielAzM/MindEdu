from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.contracts import MascotEquipIn, UserCtx
from app.services import progress_service

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/profile")
def my_profile(
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return progress_service.get_profile_summary(db, user.pk)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/dashboard")
def my_dashboard(
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return progress_service.get_home_dashboard(db, user.pk)


@router.get("/trails")
def my_trails(
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return {"items": progress_service.list_user_trails(db, user.pk)}


@router.post("/mascot/equip")
def equip_mascot_item(
    payload: MascotEquipIn,
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return progress_service.equip_mascot_item(
            db,
            user_pk=user.pk,
            mascot_id=payload.mascot_id,
            item_id=payload.item_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
