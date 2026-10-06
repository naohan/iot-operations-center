from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.anomaly import Anomaly


class AnomalyRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, device_id: int, measurement_id: int, score: float) -> Anomaly:
        anomaly = Anomaly(
            device_id=device_id,
            measurement_id=measurement_id,
            score=score,
        )
        self.db.add(anomaly)
        self.db.commit()
        self.db.refresh(anomaly)
        return anomaly

    def list_recent(self, limit: int = 50, device_id: int | None = None) -> list[Anomaly]:
        stmt = (
            select(Anomaly)
            .options(joinedload(Anomaly.device), joinedload(Anomaly.measurement))
            .order_by(Anomaly.detected_at.desc())
            .limit(limit)
        )
        if device_id is not None:
            stmt = stmt.where(Anomaly.device_id == device_id)
        return list(self.db.scalars(stmt).unique().all())

    def exists_for_measurement(self, measurement_id: int) -> bool:
        return (
            self.db.scalar(select(Anomaly.id).where(Anomaly.measurement_id == measurement_id).limit(1))
            is not None
        )
