from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.alert import Alert, AlertSeverity, AlertType


class AlertRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        device_id: int,
        alert_type: AlertType,
        severity: AlertSeverity,
        message: str,
    ) -> Alert:
        alert = Alert(
            device_id=device_id,
            type=alert_type,
            severity=severity,
            message=message,
        )
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def list_open(self, limit: int = 50) -> list[Alert]:
        stmt = (
            select(Alert)
            .options(joinedload(Alert.device))
            .where(Alert.resolved_at.is_(None))
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).unique().all())

    def list_all(self, limit: int = 50, only_open: bool = False) -> list[Alert]:
        stmt = (
            select(Alert)
            .options(joinedload(Alert.device))
            .order_by(Alert.created_at.desc())
            .limit(limit)
        )
        if only_open:
            stmt = stmt.where(Alert.resolved_at.is_(None))
        return list(self.db.scalars(stmt).unique().all())

    def get(self, alert_id: int) -> Alert | None:
        return self.db.get(Alert, alert_id)

    def resolve(self, alert: Alert) -> Alert:
        alert.resolved_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(alert)
        return alert

    def has_open_of_type(self, device_id: int, alert_type: AlertType) -> bool:
        return (
            self.db.scalar(
                select(Alert.id)
                .where(
                    Alert.device_id == device_id,
                    Alert.type == alert_type,
                    Alert.resolved_at.is_(None),
                )
                .limit(1)
            )
            is not None
        )

    def count_open(self) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(Alert).where(Alert.resolved_at.is_(None))
            )
            or 0
        )

    def count_open_critical(self) -> int:
        return int(
            self.db.scalar(
                select(func.count())
                .select_from(Alert)
                .where(
                    Alert.resolved_at.is_(None),
                    Alert.severity.in_([AlertSeverity.high, AlertSeverity.critical]),
                )
            )
            or 0
        )
