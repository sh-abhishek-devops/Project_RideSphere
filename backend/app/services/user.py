from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.domain import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate
from app.services.exceptions import ResourceConflictError
from app.services.security import hash_password


class UserService:
    def __init__(self, db: Session) -> None:
        self.user_repository = UserRepository(db)

    def create_user(self, payload: UserCreate) -> User:
        user = User(
            email=str(payload.email),
            hashed_password=hash_password(payload.password),
            first_name=payload.first_name,
            last_name=payload.last_name,
            phone_number=payload.phone_number,
            role=payload.role,
            is_active=payload.is_active,
        )

        try:
            return self.user_repository.create(user)
        except IntegrityError as exc:
            self.user_repository.db.rollback()
            raise ResourceConflictError("User with this email already exists.") from exc

    def get_user(self, user_id):
        return self.user_repository.get(user_id)

    def get_user_by_email(self, email: str) -> User | None:
        return self.user_repository.get_by_email(email)

    def list_users(self) -> list[User]:
        return self.user_repository.list()
