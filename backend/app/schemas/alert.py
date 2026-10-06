from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.alert import AlertSeverity, AlertType


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    type: AlertType
    severity: AlertSeverity
    message: str
    created_at: datetime
    resolved_at: datetime | None
    device_code: str | None = None


class AlertResolve(BaseModel):
    resolved: bool = True
