from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.schemas.user import UserCreate
from app.services.security import verify_password
from app.services.user import UserService


def test_user_service_hashes_password(db_session: Session) -> None:
    service = UserService(db_session)

    user = service.create_user(
        UserCreate(
            email="admin@example.com",
            password="SuperSecret123",
            first_name="Ada",
            last_name="Admin",
            phone_number="+15550000001",
            role=UserRole.ADMIN,
            is_active=True,
        )
    )

    assert user.hashed_password != "SuperSecret123"
    assert verify_password("SuperSecret123", user.hashed_password) is True
