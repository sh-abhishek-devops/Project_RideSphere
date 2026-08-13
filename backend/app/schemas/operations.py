from datetime import date, datetime

from pydantic import BaseModel


class OperationsDashboardResponse(BaseModel):
    date_from: date | None
    date_to: date | None
    total_ride_requests: int
    rides_searching_for_drivers: int
    active_trips: int
    completed_trips: int
    cancelled_rides: int
    available_drivers: int
    drivers_currently_on_trips: int
    payment_successes: int
    payment_failures: int
    open_support_cases: int
    generated_at: datetime
