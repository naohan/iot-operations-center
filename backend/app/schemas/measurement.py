from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MeasurementRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    timestamp: datetime
    temperature: float | None
    humidity: float | None
    pressure: float | None
    motion: bool | None
    battery: float | None
    created_at: datetime


class MeasurementWithDevice(MeasurementRead):
    device_code: str | None = None
