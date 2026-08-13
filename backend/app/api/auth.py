from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.domain import User
from app.models.enums import UserRole
from app.schemas.auth import (
    CurrentUserEnvelope,
    DriverRegistrationResponse,
    RiderRegistrationResponse,
    TokenResponse,
)
from app.schemas.driver import DriverCreate
from app.schemas.rider import RiderCreate
from app.services.auth import AuthenticationError, AuthService
from app.services.exceptions import ResourceConflictError, ResourceNotFoundError

router = APIRouter(prefix="/v1/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)


def _credentials_exception() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    service: AuthService = Depends(get_auth_service),
) -> User:
    try:
        return service.get_user_from_token(token)
    except (AuthenticationError, ResourceNotFoundError) as error:
        raise _credentials_exception() from error


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have permission to perform this action.",
            )
        return current_user

    return dependency


@router.post("/register/rider", response_model=RiderRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_rider(
    payload: RiderCreate,
    service: AuthService = Depends(get_auth_service),
) -> RiderRegistrationResponse:
    try:
        rider = service.register_rider(payload)
        return RiderRegistrationResponse(rider=rider)
    except ResourceConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/register/driver", response_model=DriverRegistrationResponse, status_code=status.HTTP_201_CREATED)
def register_driver(
    payload: DriverCreate,
    service: AuthService = Depends(get_auth_service),
) -> DriverRegistrationResponse:
    try:
        driver = service.register_driver(payload)
        return DriverRegistrationResponse(driver=driver)
    except ResourceConflictError as error:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error)) from error


@router.post("/login", response_model=TokenResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        user = service.authenticate_user(form_data.username, form_data.password)
        access_token = service.create_access_token(user)
        return TokenResponse(access_token=access_token)
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(error),
            headers={"WWW-Authenticate": "Bearer"},
        ) from error


@router.get("/me", response_model=CurrentUserEnvelope)
def get_me(current_user: User = Depends(get_current_user)) -> CurrentUserEnvelope:
    return CurrentUserEnvelope(user=current_user)
