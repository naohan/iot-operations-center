from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.device import Device, DeviceStatus
from app.repositories.alert import AlertRepository
from app.repositories.device import DeviceRepository
from app.repositories.measurement import MeasurementRepository
from app.schemas.stats import DashboardStats


class StatsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.devices = DeviceRepository(db)
        self.measurements = MeasurementRepository(db)
        self.alerts = AlertRepository(db)

    def dashboard(self) -> DashboardStats:
        total = int(self.db.scalar(select(func.count()).select_from(Device)) or 0)
        online = int(
            self.db.scalar(
                select(func.count()).select_from(Device).where(Device.status == DeviceStatus.online)
            )
            or 0
        )
        offline = int(
            self.db.scalar(
                select(func.count()).select_from(Device).where(Device.status == DeviceStatus.offline)
            )
            or 0
        )
        return DashboardStats(
            total_devices=total,
            online_devices=online,
            offline_devices=offline,
            open_alerts=self.alerts.count_open(),
            critical_alerts=self.alerts.count_open_critical(),
            measurements_last_hour=self.measurements.count_last_hour(),
        )
