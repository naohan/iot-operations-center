from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, require_roles
from app.core.security import create_access_token, verify_password
from app.database import get_db
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = UserRepository(db).get_by_email(payload.email.lower())
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    token = create_access_token(subject=user.email, role=user.role.value, user_id=user.id)
    return TokenResponse(
        access_token=token,
        role=user.role,
        email=user.email,
    )


@router.get("/me", response_model=UserRead)
def me(user: User = Depends(get_current_user)) -> User:
    return user


@router.get("/users", response_model=list[UserRead])
def list_users(
    _: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
) -> list[User]:
    return UserRepository(db).list()


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    _: User = Depends(require_roles(UserRole.admin)),
    db: Session = Depends(get_db),
) -> User:
    repo = UserRepository(db)
    if repo.get_by_email(payload.email.lower()):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User already exists")
    return repo.create(email=payload.email, password=payload.password, role=payload.role)
