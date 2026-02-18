from __future__ import annotations

from fastapi import APIRouter, Body, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, validate_payload
from app.db.session import get_db
from app.schemas.contracts import ExportReportIn, UserCtx
from app.services import report_service

router = APIRouter(prefix="/exports", tags=["exports"])


@router.post("/report")
def create_report(
    payload: dict = Body(...),
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_payload("reports", "export_create", payload)
    data = ExportReportIn.model_validate(payload)
    if data.period_end < data.period_start:
        raise HTTPException(status_code=422, detail="period_end must be >= period_start")

    try:
        result = report_service.create_report_export(db, user.pk, data.period_start, data.period_end)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="failed to generate report") from exc
    return result


@router.get("/report/{report_id}")
def get_report_status(
    report_id: str,
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        return report_service.get_export_status(db, report_id, user.pk)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/report/{report_id}/download")
def download_report(
    report_id: str,
    user: UserCtx = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    try:
        path = report_service.get_export_file(db, report_id, user.pk)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"mindedu-{report_id}.pdf",
    )
