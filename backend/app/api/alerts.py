from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.database import get_db
from app.models.user import User, UserRole
from app.repositories.alert import AlertRepository
from app.schemas.alert import AlertRead

router = APIRouter(prefix="/alerts", tags=["alerts"])


def _to_read(alert) -> AlertRead:
    return AlertRead(
        id=alert.id,
        device_id=alert.device_id,
        type=alert.type,
        severity=alert.severity,
        message=alert.message,
        created_at=alert.created_at,
        resolved_at=alert.resolved_at,
        device_code=alert.device.device_code if alert.device else None,
    )


@router.get("", response_model=list[AlertRead])
def list_alerts(
    limit: int = Query(50, ge=1, le=200),
    only_open: bool = False,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[AlertRead]:
    alerts = AlertRepository(db).list_all(limit=limit, only_open=only_open)
    return [_to_read(a) for a in alerts]


@router.post("/{alert_id}/resolve", response_model=AlertRead)
def resolve_alert(
    alert_id: int,
    _: User = Depends(require_roles(UserRole.admin, UserRole.operator)),
    db: Session = Depends(get_db),
) -> AlertRead:
    repo = AlertRepository(db)
    alert = repo.get(alert_id)
    if alert is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    if alert.resolved_at is not None:
        return _to_read(alert)
    return _to_read(repo.resolve(alert))
