from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.measurement import Measurement


class MeasurementRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(
        self,
        device_id: int,
        timestamp: datetime,
        temperature: float | None = None,
        humidity: float | None = None,
        pressure: float | None = None,
        motion: bool | None = None,
        battery: float | None = None,
    ) -> Measurement:
        measurement = Measurement(
            device_id=device_id,
            timestamp=timestamp,
            temperature=temperature,
            humidity=humidity,
            pressure=pressure,
            motion=motion,
            battery=battery,
        )
        self.db.add(measurement)
        self.db.commit()
        self.db.refresh(measurement)
        return measurement

    def list_recent(self, limit: int = 50, device_id: int | None = None) -> list[Measurement]:
        stmt = (
            select(Measurement)
            .options(joinedload(Measurement.device))
            .order_by(Measurement.timestamp.desc())
            .limit(limit)
        )
        if device_id is not None:
            stmt = stmt.where(Measurement.device_id == device_id)
        return list(self.db.scalars(stmt).unique().all())

    def count_since(self, since: datetime) -> int:
        return int(
            self.db.scalar(
                select(func.count()).select_from(Measurement).where(Measurement.timestamp >= since)
            )
            or 0
        )

    def count_last_hour(self) -> int:
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        return self.count_since(since)
