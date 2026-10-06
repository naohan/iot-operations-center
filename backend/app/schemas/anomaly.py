from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AnomalyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    measurement_id: int
    score: float
    detected_at: datetime
    device_code: str | None = None
    temperature: float | None = None


class MlStatus(BaseModel):
    enabled: bool
    algorithm: str
    min_samples: int
    contamination: float
    model_count: int
    devices_with_model: list[int]
