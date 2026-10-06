from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.device import DeviceStatus, DeviceType


class DeviceCreate(BaseModel):
    device_code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=120)
    type: DeviceType = DeviceType.multi_sensor
    location: str | None = None


class DeviceUpdate(BaseModel):
    name: str | None = None
    type: DeviceType | None = None
    location: str | None = None
    status: DeviceStatus | None = None


class DeviceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_code: str
    name: str
    type: DeviceType
    location: str | None
    status: DeviceStatus
    created_at: datetime
    last_seen_at: datetime | None
