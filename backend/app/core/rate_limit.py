from datetime import UTC, datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import Session


class RateLimiter:
    def check_and_record(
        self,
        db: Session,
        action_key: str,
        max_hits: int,
        window_seconds: int,
        user_pk: int | None,
        ip_address: str | None,
    ) -> bool:
        now = datetime.now(UTC)
        window_start = now - timedelta(seconds=window_seconds)

        result = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM api_usage_events
                WHERE action_key = :action_key
                  AND created_at >= :window_start
                  AND (
                    (:user_pk IS NOT NULL AND user_pk = :user_pk)
                    OR (:user_pk IS NULL AND :ip_address IS NOT NULL AND ip_address = :ip_address)
                  )
                """
            ),
            {
                "action_key": action_key,
                "window_start": window_start.isoformat(),
                "user_pk": user_pk,
                "ip_address": ip_address,
            },
        ).scalar_one()

        allowed = int(result) < max_hits
        if allowed:
            db.execute(
                text(
                    """
                    INSERT INTO api_usage_events (user_pk, ip_address, action_key)
                    VALUES (:user_pk, :ip_address, :action_key)
                    """
                ),
                {"user_pk": user_pk, "ip_address": ip_address, "action_key": action_key},
            )
            db.commit()
        return allowed


rate_limiter = RateLimiter()
