from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.device import Device, DeviceStatus, DeviceType
from app.schemas.device import DeviceCreate, DeviceUpdate


class DeviceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self) -> list[Device]:
        return list(self.db.scalars(select(Device).order_by(Device.device_code)).all())

    def get(self, device_id: int) -> Device | None:
        return self.db.get(Device, device_id)

    def get_by_code(self, device_code: str) -> Device | None:
        return self.db.scalar(select(Device).where(Device.device_code == device_code))

    def create(self, data: DeviceCreate) -> Device:
        device = Device(
            device_code=data.device_code,
            name=data.name,
            type=data.type,
            location=data.location,
            status=DeviceStatus.unknown,
        )
        self.db.add(device)
        self.db.commit()
        self.db.refresh(device)
        return device

    def update(self, device: Device, data: DeviceUpdate) -> Device:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(device, field, value)
        self.db.commit()
        self.db.refresh(device)
        return device

    def delete(self, device: Device) -> None:
        self.db.delete(device)
        self.db.commit()

    def upsert_from_telemetry(
        self,
        device_code: str,
        name: str | None = None,
        location: str | None = None,
        status: DeviceStatus = DeviceStatus.online,
    ) -> Device:
        device = self.get_by_code(device_code)
        now = datetime.now(timezone.utc)
        if device is None:
            device = Device(
                device_code=device_code,
                name=name or device_code,
                type=DeviceType.multi_sensor,
                location=location,
                status=status,
                last_seen_at=now,
            )
            self.db.add(device)
        else:
            device.status = status
            device.last_seen_at = now
            if name:
                device.name = name
            if location:
                device.location = location
        self.db.commit()
        self.db.refresh(device)
        return device
