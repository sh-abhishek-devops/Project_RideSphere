from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.domain import Rider
from app.models.enums import UserRole
from app.repositories.rider import RiderRepository
from app.schemas.rider import RiderCreate
from app.schemas.user import UserCreate
from app.services.exceptions import ResourceConflictError
from app.services.user import UserService


class RiderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.rider_repository = RiderRepository(db)
        self.user_service = UserService(db)

    def create_rider(self, payload: RiderCreate) -> Rider:
        user = self.user_service.create_user(
            UserCreate(role=UserRole.RIDER, **payload.user.model_dump())
        )
        rider = Rider(user_id=user.id)

        try:
            return self.rider_repository.create(rider)
        except IntegrityError as exc:
            self.db.rollback()
            raise ResourceConflictError("Rider profile could not be created.") from exc

    def get_rider(self, rider_id):
        return self.rider_repository.get(rider_id)

    def list_riders(self) -> list[Rider]:
        return self.rider_repository.list()
