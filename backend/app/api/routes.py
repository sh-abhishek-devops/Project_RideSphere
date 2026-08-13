from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.auth import require_roles
from app.api.auth import router as auth_router
from app.core.config import get_settings
from app.database.health import get_database_health
from app.database.session import get_db
from app.models.domain import User
from app.models.enums import UserRole
from app.schemas.driver import DriverCreate, DriverResponse
from app.schemas.driver_availability import (
    DriverAvailabilityCreate,
    DriverAvailabilityResponse,
    DriverSelfAvailabilityUpdate,
)
from app.schemas.health import HealthResponse
from app.schemas.operations import OperationsDashboardResponse
from app.schemas.payment import PaymentResponse
from app.schemas.ride_request import RideRequestCreate, RideRequestResponse
from app.schemas.rider import RiderCreate, RiderResponse
from app.schemas.support_case import (
    SupportAgentSummary,
    SupportCaseCreate,
    SupportCaseResolve,
    SupportCaseResponse,
    SupportCaseUpdate,
    SupportInvestigationResponse,
)
from app.schemas.trip import TripCompletionRequest, TripResponse
from app.schemas.user import UserCreate, UserResponse
from app.schemas.vehicle import VehicleCreate, VehicleResponse
from app.services.driver import DriverService
from app.services.driver_availability import DriverAvailabilityService
from app.services.exceptions import ResourceConflictError, ResourceNotFoundError
from app.services.operations import OperationsDashboardService
from app.services.payment import PaymentService
from app.services.ride_request import RideRequestService
from app.services.rider import RiderService
from app.services.support_case import SupportCaseService
from app.services.trip import TripService
from app.services.user import UserService
from app.services.vehicle import VehicleService

router = APIRouter()
router.include_router(auth_router)


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)


def get_rider_service(db: Session = Depends(get_db)) -> RiderService:
    return RiderService(db)


def get_driver_service(db: Session = Depends(get_db)) -> DriverService:
    return DriverService(db)


def get_vehicle_service(db: Session = Depends(get_db)) -> VehicleService:
    return VehicleService(db)


def get_driver_availability_service(
    db: Session = Depends(get_db),
) -> DriverAvailabilityService:
    return DriverAvailabilityService(db)


def get_ride_request_service(db: Session = Depends(get_db)) -> RideRequestService:
    return RideRequestService(db)


def get_trip_service(db: Session = Depends(get_db)) -> TripService:
    return TripService(db)


def get_payment_service(db: Session = Depends(get_db)) -> PaymentService:
    return PaymentService(db)


def get_operations_dashboard_service(db: Session = Depends(get_db)) -> OperationsDashboardService:
    return OperationsDashboardService(db)


def get_support_case_service(db: Session = Depends(get_db)) -> SupportCaseService:
    return SupportCaseService(db)


def raise_from_service_error(error: Exception) -> None:
    if isinstance(error, ResourceConflictError):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error
    if isinstance(error, ResourceNotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error)) from error
    raise error


@router.get("/health", response_model=HealthResponse, tags=["health"])
def health_check() -> HealthResponse:
    settings = get_settings()
    database_health = get_database_health()
    application_status = "healthy" if database_health.status == "healthy" else "degraded"

    return HealthResponse(
        status=application_status,
        application=settings.app_name,
        database=database_health,
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["users"])
def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> UserResponse:
    try:
        return service.create_user(payload)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/users", response_model=list[UserResponse], tags=["users"])
def list_users(
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> list[UserResponse]:
    return service.list_users()


@router.get("/users/{user_id}", response_model=UserResponse, tags=["users"])
def get_user(
    user_id: UUID,
    service: UserService = Depends(get_user_service),
    _: User = Depends(require_roles(UserRole.ADMIN)),
) -> UserResponse:
    user = service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return user


@router.post("/riders", response_model=RiderResponse, status_code=status.HTTP_201_CREATED, tags=["riders"])
def create_rider(
    payload: RiderCreate,
    service: RiderService = Depends(get_rider_service),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER)),
) -> RiderResponse:
    try:
        return service.create_rider(payload)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/riders", response_model=list[RiderResponse], tags=["riders"])
def list_riders(
    service: RiderService = Depends(get_rider_service),
    _: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.SUPPORT_AGENT)
    ),
) -> list[RiderResponse]:
    return service.list_riders()


@router.get("/riders/{rider_id}", response_model=RiderResponse, tags=["riders"])
def get_rider(
    rider_id: UUID,
    service: RiderService = Depends(get_rider_service),
    _: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.SUPPORT_AGENT)
    ),
) -> RiderResponse:
    rider = service.get_rider(rider_id)
    if rider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Rider not found.")
    return rider


@router.post("/drivers", response_model=DriverResponse, status_code=status.HTTP_201_CREATED, tags=["drivers"])
def create_driver(
    payload: DriverCreate,
    service: DriverService = Depends(get_driver_service),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER)),
) -> DriverResponse:
    try:
        return service.create_driver(payload)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/drivers", response_model=list[DriverResponse], tags=["drivers"])
def list_drivers(
    service: DriverService = Depends(get_driver_service),
    _: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.SUPPORT_AGENT)
    ),
) -> list[DriverResponse]:
    return service.list_drivers()


@router.get("/drivers/{driver_id}", response_model=DriverResponse, tags=["drivers"])
def get_driver(
    driver_id: UUID,
    service: DriverService = Depends(get_driver_service),
    _: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.SUPPORT_AGENT)
    ),
) -> DriverResponse:
    driver = service.get_driver(driver_id)
    if driver is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found.")
    return driver


@router.post("/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED, tags=["vehicles"])
def create_vehicle(
    payload: VehicleCreate,
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.DRIVER)),
) -> VehicleResponse:
    try:
        return service.create_vehicle(payload)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/vehicles", response_model=list[VehicleResponse], tags=["vehicles"])
def list_vehicles(
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.SUPPORT_AGENT)
    ),
) -> list[VehicleResponse]:
    return service.list_vehicles()


@router.get("/vehicles/{vehicle_id}", response_model=VehicleResponse, tags=["vehicles"])
def get_vehicle(
    vehicle_id: UUID,
    service: VehicleService = Depends(get_vehicle_service),
    _: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.SUPPORT_AGENT)
    ),
) -> VehicleResponse:
    vehicle = service.get_vehicle(vehicle_id)
    if vehicle is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found.")
    return vehicle


@router.post(
    "/driver-availabilities",
    response_model=DriverAvailabilityResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["driver-availabilities"],
)
def create_driver_availability(
    payload: DriverAvailabilityCreate,
    service: DriverAvailabilityService = Depends(get_driver_availability_service),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.DRIVER)),
) -> DriverAvailabilityResponse:
    try:
        return service.create_driver_availability(payload)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get(
    "/driver-availabilities",
    response_model=list[DriverAvailabilityResponse],
    tags=["driver-availabilities"],
)
def list_driver_availabilities(
    service: DriverAvailabilityService = Depends(get_driver_availability_service),
    _: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.SUPPORT_AGENT)
    ),
) -> list[DriverAvailabilityResponse]:
    return service.list_driver_availabilities()


@router.get(
    "/driver-availabilities/{availability_id}",
    response_model=DriverAvailabilityResponse,
    tags=["driver-availabilities"],
)
def get_driver_availability(
    availability_id: UUID,
    service: DriverAvailabilityService = Depends(get_driver_availability_service),
    _: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.OPERATIONS_MANAGER, UserRole.SUPPORT_AGENT)
    ),
) -> DriverAvailabilityResponse:
    availability = service.get_driver_availability(availability_id)
    if availability is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver availability not found.",
    )
    return availability


@router.put("/v1/drivers/me/availability", response_model=DriverAvailabilityResponse, tags=["drivers"])
def update_my_driver_availability(
    payload: DriverSelfAvailabilityUpdate,
    service: DriverAvailabilityService = Depends(get_driver_availability_service),
    current_user: User = Depends(require_roles(UserRole.DRIVER)),
) -> DriverAvailabilityResponse:
    try:
        return service.update_my_availability(current_user, payload)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/drivers/me/availability", response_model=DriverAvailabilityResponse, tags=["drivers"])
def get_my_driver_availability(
    service: DriverAvailabilityService = Depends(get_driver_availability_service),
    current_user: User = Depends(require_roles(UserRole.DRIVER)),
) -> DriverAvailabilityResponse:
    try:
        return service.get_my_availability(current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/drivers/me/ride-offers", response_model=list[RideRequestResponse], tags=["drivers"])
def list_my_driver_ride_offers(
    service: RideRequestService = Depends(get_ride_request_service),
    current_user: User = Depends(require_roles(UserRole.DRIVER)),
) -> list[RideRequestResponse]:
    try:
        return service.list_driver_ride_offers(current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.post("/v1/drivers/me/ride-offers/{ride_id}/accept", response_model=RideRequestResponse, tags=["drivers"])
def accept_driver_ride_offer(
    ride_id: UUID,
    service: RideRequestService = Depends(get_ride_request_service),
    current_user: User = Depends(require_roles(UserRole.DRIVER)),
) -> RideRequestResponse:
    try:
        return service.accept_driver_ride_offer(ride_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.post(
    "/v1/rides",
    response_model=RideRequestResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["rides"],
)
def create_ride_request(
    payload: RideRequestCreate,
    service: RideRequestService = Depends(get_ride_request_service),
    current_user: User = Depends(require_roles(UserRole.RIDER)),
) -> RideRequestResponse:
    try:
        return service.create_ride_request(current_user, payload)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/rides/{ride_id}", response_model=RideRequestResponse, tags=["rides"])
def get_ride_request(
    ride_id: UUID,
    service: RideRequestService = Depends(get_ride_request_service),
    current_user: User = Depends(
        require_roles(
            UserRole.RIDER,
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> RideRequestResponse:
    try:
        return service.get_ride_request(ride_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/rides", response_model=list[RideRequestResponse], tags=["rides"])
def list_ride_requests(
    service: RideRequestService = Depends(get_ride_request_service),
    current_user: User = Depends(
        require_roles(
            UserRole.RIDER,
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> list[RideRequestResponse]:
    try:
        return service.list_ride_requests(current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.post("/v1/rides/{ride_id}/cancel", response_model=RideRequestResponse, tags=["rides"])
def cancel_ride_request(
    ride_id: UUID,
    service: RideRequestService = Depends(get_ride_request_service),
    current_user: User = Depends(
        require_roles(
            UserRole.RIDER,
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> RideRequestResponse:
    try:
        return service.cancel_ride_request(ride_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/trips/{trip_id}", response_model=TripResponse, tags=["trips"])
def get_trip(
    trip_id: UUID,
    service: TripService = Depends(get_trip_service),
    current_user: User = Depends(
        require_roles(
            UserRole.RIDER,
            UserRole.DRIVER,
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> TripResponse:
    try:
        return service.get_trip(trip_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/drivers/me/trips", response_model=list[TripResponse], tags=["drivers"])
def list_my_driver_trips(
    service: TripService = Depends(get_trip_service),
    current_user: User = Depends(require_roles(UserRole.DRIVER)),
) -> list[TripResponse]:
    try:
        return service.list_driver_trips(current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.post("/v1/trips/{trip_id}/en-route", response_model=TripResponse, tags=["trips"])
def mark_trip_en_route(
    trip_id: UUID,
    service: TripService = Depends(get_trip_service),
    current_user: User = Depends(require_roles(UserRole.DRIVER)),
) -> TripResponse:
    try:
        return service.mark_en_route(trip_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.post("/v1/trips/{trip_id}/arrived", response_model=TripResponse, tags=["trips"])
def mark_trip_arrived(
    trip_id: UUID,
    service: TripService = Depends(get_trip_service),
    current_user: User = Depends(require_roles(UserRole.DRIVER)),
) -> TripResponse:
    try:
        return service.mark_arrived(trip_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.post("/v1/trips/{trip_id}/start", response_model=TripResponse, tags=["trips"])
def start_trip(
    trip_id: UUID,
    service: TripService = Depends(get_trip_service),
    current_user: User = Depends(require_roles(UserRole.DRIVER)),
) -> TripResponse:
    try:
        return service.start_trip(trip_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.post("/v1/trips/{trip_id}/complete", response_model=TripResponse, tags=["trips"])
def complete_trip(
    trip_id: UUID,
    payload: TripCompletionRequest,
    service: TripService = Depends(get_trip_service),
    current_user: User = Depends(require_roles(UserRole.DRIVER)),
) -> TripResponse:
    try:
        return service.complete_trip(
            trip_id,
            current_user,
            actual_distance=payload.actual_distance,
            actual_duration=payload.actual_duration,
        )
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/payments/{payment_id}", response_model=PaymentResponse, tags=["payments"])
def get_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(
        require_roles(
            UserRole.RIDER,
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> PaymentResponse:
    try:
        return service.get_payment(payment_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/trips/{trip_id}/payment", response_model=PaymentResponse, tags=["payments"])
def get_trip_payment(
    trip_id: UUID,
    service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(
        require_roles(
            UserRole.RIDER,
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> PaymentResponse:
    try:
        return service.get_trip_payment(trip_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.post("/v1/payments/{payment_id}/refund", response_model=PaymentResponse, tags=["payments"])
def refund_payment(
    payment_id: UUID,
    service: PaymentService = Depends(get_payment_service),
    current_user: User = Depends(
        require_roles(UserRole.PAYMENT_AGENT, UserRole.OPERATIONS_MANAGER, UserRole.ADMIN)
    ),
) -> PaymentResponse:
    try:
        return service.refund_payment(payment_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/operations/dashboard", response_model=OperationsDashboardResponse, tags=["operations"])
def get_operations_dashboard(
    date_from: date | None = None,
    date_to: date | None = None,
    service: OperationsDashboardService = Depends(get_operations_dashboard_service),
    _: User = Depends(require_roles(UserRole.OPERATIONS_MANAGER, UserRole.ADMIN)),
) -> OperationsDashboardResponse:
    try:
        return service.get_dashboard_metrics(date_from=date_from, date_to=date_to)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/support/agents", response_model=list[SupportAgentSummary], tags=["support"])
def list_support_agents(
    service: SupportCaseService = Depends(get_support_case_service),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> list[SupportAgentSummary]:
    try:
        return service.list_assignable_agents(current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.post("/v1/support/cases", response_model=SupportCaseResponse, status_code=status.HTTP_201_CREATED, tags=["support"])
def create_support_case(
    payload: SupportCaseCreate,
    service: SupportCaseService = Depends(get_support_case_service),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> SupportCaseResponse:
    try:
        return service.create_support_case(current_user, payload)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/support/cases", response_model=list[SupportCaseResponse], tags=["support"])
def list_support_cases(
    service: SupportCaseService = Depends(get_support_case_service),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> list[SupportCaseResponse]:
    try:
        return service.list_support_cases(current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/support/cases/{case_id}", response_model=SupportCaseResponse, tags=["support"])
def get_support_case(
    case_id: UUID,
    service: SupportCaseService = Depends(get_support_case_service),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> SupportCaseResponse:
    try:
        return service.get_support_case(case_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.patch("/v1/support/cases/{case_id}", response_model=SupportCaseResponse, tags=["support"])
def update_support_case(
    case_id: UUID,
    payload: SupportCaseUpdate,
    service: SupportCaseService = Depends(get_support_case_service),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> SupportCaseResponse:
    try:
        return service.update_support_case(case_id, current_user, payload)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.post("/v1/support/cases/{case_id}/resolve", response_model=SupportCaseResponse, tags=["support"])
def resolve_support_case(
    case_id: UUID,
    payload: SupportCaseResolve,
    service: SupportCaseService = Depends(get_support_case_service),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> SupportCaseResponse:
    try:
        return service.resolve_support_case(case_id, current_user, payload)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)


@router.get("/v1/support/cases/{case_id}/investigation", response_model=SupportInvestigationResponse, tags=["support"])
def get_support_investigation(
    case_id: UUID,
    service: SupportCaseService = Depends(get_support_case_service),
    current_user: User = Depends(
        require_roles(
            UserRole.SUPPORT_AGENT,
            UserRole.PAYMENT_AGENT,
            UserRole.OPERATIONS_MANAGER,
            UserRole.ADMIN,
        )
    ),
) -> SupportInvestigationResponse:
    try:
        return service.get_investigation(case_id, current_user)
    except Exception as error:  # pragma: no cover - narrowed by helper
        raise_from_service_error(error)
