from app.config import get_settings
from app.database import SessionLocal
from app.models.user import UserRole
from app.repositories.user import UserRepository


def seed_users() -> None:
    settings = get_settings()
    db = SessionLocal()
    try:
        repo = UserRepository(db)
        repo.ensure_user(settings.seed_admin_email, settings.seed_admin_password, UserRole.admin)
        repo.ensure_user(
            settings.seed_operator_email,
            settings.seed_operator_password,
            UserRole.operator,
        )
        repo.ensure_user(
            settings.seed_viewer_email,
            settings.seed_viewer_password,
            UserRole.viewer,
        )
    finally:
        db.close()
