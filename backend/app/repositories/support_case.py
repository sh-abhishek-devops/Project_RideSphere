from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.domain import SupportCase, Trip
from app.repositories.base import BaseRepository


class SupportCaseRepository(BaseRepository[SupportCase]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, SupportCase)

    def _base_query(self):
        return (
            select(SupportCase)
            .options(
                selectinload(SupportCase.ride_request),
                selectinload(SupportCase.trip).selectinload(Trip.status_history),
                selectinload(SupportCase.created_by_user),
                selectinload(SupportCase.assigned_agent_user),
            )
            .execution_options(populate_existing=True)
        )

    def get(self, entity_id: UUID):  # type: ignore[override]
        return self.db.scalar(self._base_query().where(SupportCase.id == entity_id))

    def list(self) -> list[SupportCase]:  # type: ignore[override]
        return list(self.db.scalars(self._base_query().order_by(SupportCase.updated_at.desc())))
