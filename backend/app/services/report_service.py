from __future__ import annotations

import json
from collections import Counter
from datetime import date
from pathlib import Path
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.utils.pdf_builder import build_educational_report

EXPORT_DIR = Path(get_settings().export_dir)


def create_report_export(db: Session, user_pk: int, period_start: date, period_end: date) -> dict[str, str]:
    report_id = f"rpt_{uuid4().hex[:12]}"
    db.execute(
        text(
            """
            INSERT INTO exports_reports (report_id, requested_by_user_pk, period_start, period_end, status)
            VALUES (:report_id, :requested_by_user_pk, :period_start, :period_end, 'processing')
            """
        ),
        {
            "report_id": report_id,
            "requested_by_user_pk": user_pk,
            "period_start": str(period_start),
            "period_end": str(period_end),
        },
    )
    db.commit()

    try:
        summary = _build_summary(db, user_pk, period_start, period_end)
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        pdf_path = EXPORT_DIR / f"{report_id}.pdf"

        lines = [
            f"Período: {period_start} até {period_end}",
            "",
            f"Trilhas concluídas: {summary['trails_completed']}",
            f"Lições concluídas: {summary['lessons_completed']}",
            f"Tentativas de quiz: {summary['quiz_attempts']}",
            "",
            "Técnicas aprendidas:",
        ]
        lines.extend([f"- {item}" for item in summary["techniques"]])
        lines.extend(
            [
                "",
                f"Check-ins registrados: {summary['checkins_count']}",
                f"Missões criadas: {summary['missions_created']}",
                f"Respostas úteis recebidas: {summary['useful_feedback_received']}",
                "",
                "Este relatório é educativo, agregado e não diagnóstico.",
            ]
        )

        build_educational_report(pdf_path, "Relatório Educativo MindEdu", lines)

        db.execute(
            text(
                """
                UPDATE exports_reports
                SET status = 'ready', file_path = :file_path, summary_json = :summary_json
                WHERE report_id = :report_id
                """
            ),
            {
                "report_id": report_id,
                "file_path": str(pdf_path),
                "summary_json": json.dumps(summary),
            },
        )
        db.commit()
    except Exception:
        db.execute(
            text("UPDATE exports_reports SET status='failed' WHERE report_id=:report_id"),
            {"report_id": report_id},
        )
        db.commit()
        raise

    return {"report_id": report_id, "status": "ready"}


def _build_summary(db: Session, user_pk: int, period_start: date, period_end: date) -> dict:
    bounds = {
        "user_pk": user_pk,
        "start": str(period_start),
        "end": str(period_end),
    }

    lessons_completed = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM lesson_completion
                WHERE user_pk = :user_pk
                  AND DATE(completed_at) BETWEEN :start AND :end
                """
            ),
            bounds,
        ).scalar_one()
    )

    trails_completed = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM (
                    SELECT l.trail_id, COUNT(*) AS completed_lessons, (
                        SELECT COUNT(*) FROM lessons all_l WHERE all_l.trail_id = l.trail_id
                    ) AS total_lessons
                    FROM lesson_completion lc
                    JOIN lessons l ON l.id = lc.lesson_id
                    WHERE lc.user_pk = :user_pk
                      AND DATE(lc.completed_at) BETWEEN :start AND :end
                    GROUP BY l.trail_id
                ) q
                WHERE q.completed_lessons >= q.total_lessons AND q.total_lessons > 0
                """
            ),
            bounds,
        ).scalar_one()
    )

    quiz_attempts = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM quiz_attempts
                WHERE user_pk = :user_pk
                  AND DATE(created_at) BETWEEN :start AND :end
                """
            ),
            bounds,
        ).scalar_one()
    )

    checkins = db.execute(
        text(
            """
            SELECT need_tags_json
            FROM emotion_checkins
            WHERE user_pk = :user_pk
              AND DATE(created_at) BETWEEN :start AND :end
            """
        ),
        bounds,
    ).mappings().all()

    technique_counter: Counter[str] = Counter()
    for row in checkins:
        for tag in json.loads(row["need_tags_json"]):
            technique_counter[tag] += 1

    missions_created = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM missions
                WHERE creator_user_pk = :user_pk
                  AND DATE(created_at) BETWEEN :start AND :end
                """
            ),
            bounds,
        ).scalar_one()
    )

    useful_feedback_received = int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM mission_feedback mf
                JOIN mission_responses mr ON mr.id = mf.response_id
                WHERE mr.responder_user_pk = :user_pk
                  AND mf.is_useful = 1
                  AND DATE(mf.created_at) BETWEEN :start AND :end
                """
            ),
            bounds,
        ).scalar_one()
    )

    return {
        "trails_completed": trails_completed,
        "lessons_completed": lessons_completed,
        "quiz_attempts": quiz_attempts,
        "techniques": [name for name, _ in technique_counter.most_common(5)] or ["respirar_1_min"],
        "checkins_count": len(checkins),
        "missions_created": missions_created,
        "useful_feedback_received": useful_feedback_received,
    }


def get_export_status(db: Session, report_id: str, user_pk: int) -> dict:
    row = db.execute(
        text(
            """
            SELECT report_id, status, file_path
            FROM exports_reports
            WHERE report_id = :report_id AND requested_by_user_pk = :user_pk
            """
        ),
        {"report_id": report_id, "user_pk": user_pk},
    ).mappings().first()
    if not row:
        raise ValueError("report not found")

    payload = {"report_id": row["report_id"], "status": row["status"]}
    if row["status"] == "ready":
        payload["download_url"] = f"/exports/report/{row['report_id']}/download"
    return payload


def get_export_file(db: Session, report_id: str, user_pk: int) -> Path:
    row = db.execute(
        text(
            """
            SELECT file_path, status
            FROM exports_reports
            WHERE report_id = :report_id AND requested_by_user_pk = :user_pk
            """
        ),
        {"report_id": report_id, "user_pk": user_pk},
    ).mappings().first()
    if not row:
        raise ValueError("report not found")
    if row["status"] != "ready" or not row["file_path"]:
        raise ValueError("report not ready")

    file_path = Path(row["file_path"])
    if not file_path.exists():
        raise ValueError("report file missing")
    return file_path

