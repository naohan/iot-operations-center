from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.stats import DashboardStats, HealthResponse
from app.services.stats import StatsService

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="iot-api")


@router.get("/stats/dashboard", response_model=DashboardStats)
def dashboard_stats(
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardStats:
    return StatsService(db).dashboard()
