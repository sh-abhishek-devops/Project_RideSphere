from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.domain import DriverAvailability, Payment, RideRequest, SupportCase, Trip
from app.models.enums import (
    AvailabilityStatus,
    PaymentStatus,
    RideRequestStatus,
    SupportCaseStatus,
    TripStatus,
)
from app.schemas.operations import OperationsDashboardResponse
from app.services.exceptions import ResourceConflictError


class OperationsDashboardService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_dashboard_metrics(
        self,
        *,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> OperationsDashboardResponse:
        start_at, end_at = self._build_range(date_from, date_to)

        return OperationsDashboardResponse(
            date_from=date_from,
            date_to=date_to,
            total_ride_requests=self._count_rides(start_at, end_at),
            rides_searching_for_drivers=self._count_rides(
                start_at,
                end_at,
                RideRequest.status == RideRequestStatus.SEARCHING_DRIVER,
            ),
            active_trips=self._count_trips(
                start_at,
                end_at,
                Trip.status.not_in([TripStatus.TRIP_COMPLETED, TripStatus.CANCELLED]),
            ),
            completed_trips=self._count_trips(
                start_at,
                end_at,
                Trip.status == TripStatus.TRIP_COMPLETED,
            ),
            cancelled_rides=self._count_rides(
                start_at,
                end_at,
                RideRequest.status == RideRequestStatus.CANCELLED,
            ),
            available_drivers=self._count_latest_driver_status(
                start_at,
                end_at,
                AvailabilityStatus.AVAILABLE,
            ),
            drivers_currently_on_trips=self._count_latest_driver_status(
                start_at,
                end_at,
                AvailabilityStatus.ON_TRIP,
            ),
            payment_successes=self._count_payments(
                start_at,
                end_at,
                Payment.status == PaymentStatus.SUCCESS,
            ),
            payment_failures=self._count_payments(
                start_at,
                end_at,
                Payment.status == PaymentStatus.FAILED,
            ),
            open_support_cases=self._count_support_cases(
                start_at,
                end_at,
                SupportCase.status != SupportCaseStatus.RESOLVED,
            ),
            generated_at=datetime.now(UTC),
        )

    @staticmethod
    def _build_range(date_from: date | None, date_to: date | None) -> tuple[datetime | None, datetime | None]:
        if date_from and date_to and date_to < date_from:
            raise ResourceConflictError("date_to must be greater than or equal to date_from.")

        start_at = datetime.combine(date_from, time.min, tzinfo=UTC) if date_from else None
        end_at = datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=UTC) if date_to else None
        return start_at, end_at

    def _count_rides(self, start_at: datetime | None, end_at: datetime | None, *conditions) -> int:
        query = select(func.count(RideRequest.id))
        query = self._apply_range(query, RideRequest.requested_at, start_at, end_at)
        for condition in conditions:
            query = query.where(condition)
        return int(self.db.scalar(query) or 0)

    def _count_trips(self, start_at: datetime | None, end_at: datetime | None, *conditions) -> int:
        query = select(func.count(Trip.id))
        query = self._apply_range(query, Trip.created_at, start_at, end_at)
        for condition in conditions:
            query = query.where(condition)
        return int(self.db.scalar(query) or 0)

    def _count_payments(self, start_at: datetime | None, end_at: datetime | None, *conditions) -> int:
        query = select(func.count(Payment.id))
        query = self._apply_range(query, Payment.created_at, start_at, end_at)
        for condition in conditions:
            query = query.where(condition)
        return int(self.db.scalar(query) or 0)

    def _count_support_cases(self, start_at: datetime | None, end_at: datetime | None, *conditions) -> int:
        query = select(func.count(SupportCase.id))
        query = self._apply_range(query, SupportCase.created_at, start_at, end_at)
        for condition in conditions:
            query = query.where(condition)
        return int(self.db.scalar(query) or 0)

    def _count_latest_driver_status(
        self,
        start_at: datetime | None,
        end_at: datetime | None,
        status: AvailabilityStatus,
    ) -> int:
        latest_availability_subquery = (
            select(
                DriverAvailability.driver_id.label("driver_id"),
                func.max(DriverAvailability.updated_at).label("latest_updated_at"),
            )
            .group_by(DriverAvailability.driver_id)
            .subquery()
        )

        query = (
            select(func.count(DriverAvailability.id))
            .select_from(DriverAvailability)
            .join(
                latest_availability_subquery,
                (DriverAvailability.driver_id == latest_availability_subquery.c.driver_id)
                & (DriverAvailability.updated_at == latest_availability_subquery.c.latest_updated_at),
            )
            .where(DriverAvailability.status == status)
        )
        query = self._apply_range(query, DriverAvailability.updated_at, start_at, end_at)
        return int(self.db.scalar(query) or 0)

    @staticmethod
    def _apply_range(query, column, start_at: datetime | None, end_at: datetime | None):
        if start_at is not None:
            query = query.where(column >= start_at)
        if end_at is not None:
            query = query.where(column < end_at)
        return query
