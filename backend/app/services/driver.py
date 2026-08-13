from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.domain import Driver
from app.models.enums import UserRole
from app.repositories.driver import DriverRepository
from app.schemas.driver import DriverCreate
from app.schemas.user import UserCreate
from app.services.exceptions import ResourceConflictError
from app.services.user import UserService


class DriverService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.driver_repository = DriverRepository(db)
        self.user_service = UserService(db)

    def create_driver(self, payload: DriverCreate) -> Driver:
        user = self.user_service.create_user(
            UserCreate(role=UserRole.DRIVER, **payload.user.model_dump())
        )
        driver = Driver(user_id=user.id)

        try:
            return self.driver_repository.create(driver)
        except IntegrityError as exc:
            self.db.rollback()
            raise ResourceConflictError("Driver profile could not be created.") from exc

    def get_driver(self, driver_id):
        return self.driver_repository.get(driver_id)

    def list_drivers(self) -> list[Driver]:
        return self.driver_repository.list()
