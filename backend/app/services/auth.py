from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from jwt import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.domain import User
from app.repositories.user import UserRepository
from app.schemas.driver import DriverCreate
from app.schemas.rider import RiderCreate
from app.services.driver import DriverService
from app.services.exceptions import ResourceNotFoundError
from app.services.rider import RiderService
from app.services.security import verify_password


class AuthenticationError(Exception):
    pass


class AuthorizationError(Exception):
    pass


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.settings = get_settings()
        self.user_repository = UserRepository(db)
        self.rider_service = RiderService(db)
        self.driver_service = DriverService(db)

    def register_rider(self, payload: RiderCreate):
        return self.rider_service.create_rider(payload)

    def register_driver(self, payload: DriverCreate):
        return self.driver_service.create_driver(payload)

    def authenticate_user(self, email: str, password: str) -> User:
        user = self.user_repository.get_by_email(email)
        if user is None or verify_password(password, user.hashed_password) is False:
            raise AuthenticationError("Incorrect email or password.")
        if user.is_active is False:
            raise AuthenticationError("Inactive user.")
        return user

    def create_access_token(self, user: User) -> str:
        expires_delta = timedelta(minutes=self.settings.access_token_expire_minutes)
        expire_at = datetime.now(UTC) + expires_delta
        payload = {
            "sub": str(user.id),
            "role": user.role.value,
            "exp": expire_at,
        }
        return jwt.encode(
            payload,
            self.settings.jwt_secret_key,
            algorithm=self.settings.jwt_algorithm,
        )

    def decode_access_token(self, token: str) -> dict:
        try:
            return jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.settings.jwt_algorithm],
            )
        except InvalidTokenError as exc:
            raise AuthenticationError("Invalid authentication credentials.") from exc

    def get_user_from_token(self, token: str) -> User:
        payload = self.decode_access_token(token)
        subject = payload.get("sub")

        if subject is None:
            raise AuthenticationError("Invalid authentication credentials.")

        try:
            user_id = UUID(subject)
        except ValueError as exc:
            raise AuthenticationError("Invalid authentication credentials.") from exc

        user = self.user_repository.get(user_id)
        if user is None:
            raise ResourceNotFoundError("Authenticated user not found.")
        if user.is_active is False:
            raise AuthenticationError("Inactive user.")
        return user
