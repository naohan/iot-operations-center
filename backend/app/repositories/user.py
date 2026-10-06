from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def list(self) -> list[User]:
        return list(self.db.scalars(select(User).order_by(User.email)).all())

    def create(self, email: str, password: str, role: UserRole) -> User:
        user = User(
            email=email.lower().strip(),
            password_hash=hash_password(password),
            role=role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def ensure_user(self, email: str, password: str, role: UserRole) -> User:
        existing = self.get_by_email(email)
        if existing:
            return existing
        return self.create(email=email, password=password, role=role)
