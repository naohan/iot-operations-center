from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    service: str


class DashboardStats(BaseModel):
    total_devices: int
    online_devices: int
    offline_devices: int
    open_alerts: int
    critical_alerts: int
    measurements_last_hour: int
