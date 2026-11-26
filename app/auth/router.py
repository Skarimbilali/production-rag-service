
"""
Authentication API endpoints.

Features:
- User signup
- User login
- JWT access token
- Refresh token rotation
- Logout
- Current authenticated user
"""

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.auth.database import AuthDatabase
from app.auth.schemas import (
    AuthResponse,
    LoginRequest,
    MessageResponse,
    SignupRequest,
    UserResponse,
)
from app.auth.security import AuthSecurity
from app.config import settings


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

auth_database = AuthDatabase()

bearer_scheme = HTTPBearer(auto_error=False)

REFRESH_COOKIE_NAME = "rag_refresh_token"


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def set_refresh_cookie(
    response: Response,
    refresh_token: str,
) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        max_age=settings.JWT_REFRESH_TOKEN_DAYS * 86400,
        path="/auth",
        httponly=True,
        secure=settings.AUTH_COOKIE_SECURE,
        samesite="lax",
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/auth",
        secure=settings.AUTH_COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )


def create_login_session(
    user: dict,
    response: Response,
) -> AuthResponse:
    access_token, _ = AuthSecurity.create_access_token(
        user["id"]
    )

    refresh_token, refresh_expires_at = (
        AuthSecurity.create_refresh_token(user["id"])
    )

    auth_database.create_session(
        user_id=user["id"],
        refresh_token=refresh_token,
        expires_at=refresh_expires_at,
    )

    set_refresh_cookie(response, refresh_token)

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_MINUTES * 60,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
        ),
    )


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(
        bearer_scheme
    ),
) -> dict:
    """
    Dependency for protected API endpoints.

    Requires:
        Authorization: Bearer <access_token>
    """
    if (
        credentials is None
        or credentials.scheme.lower() != "bearer"
    ):
        raise unauthorized()

    user_id = AuthSecurity.verify_access_token(
        credentials.credentials
    )

    if not user_id:
        raise unauthorized()

    user = auth_database.get_user_by_id(user_id)

    if user is None:
        raise unauthorized()

    return user


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def signup(
    request: SignupRequest,
    response: Response,
) -> AuthResponse:
    password_hash = AuthSecurity.hash_password(
        request.password
    )

    user = auth_database.create_user(
        email=str(request.email),
        password_hash=password_hash,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    return create_login_session(user, response)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="Login with email and password",
)
def login(
    request: LoginRequest,
    response: Response,
) -> AuthResponse:
    user = auth_database.get_user_by_email(
        str(request.email)
    )

    # Do not reveal whether an email exists.
    if user is None:
        raise unauthorized()

    if not AuthSecurity.verify_password(
        request.password,
        user["password_hash"],
    ):
        raise unauthorized()

    return create_login_session(user, response)


@router.post(
    "/refresh",
    response_model=AuthResponse,
    summary="Refresh an authenticated session",
)
def refresh_session(
    request: Request,
    response: Response,
) -> AuthResponse:
    refresh_token = request.cookies.get(
        REFRESH_COOKIE_NAME
    )

    if not refresh_token:
        raise unauthorized()

    user_id = AuthSecurity.verify_refresh_token(
        refresh_token
    )

    if not user_id:
        raise unauthorized()

    session = auth_database.get_active_session(
        refresh_token
    )

    if session is None or session["user_id"] != user_id:
        raise unauthorized()

    user = auth_database.get_user_by_id(user_id)

    if user is None:
        raise unauthorized()

    new_refresh_token, new_expiry = (
        AuthSecurity.create_refresh_token(user_id)
    )

    rotated = auth_database.rotate_session(
        old_refresh_token=refresh_token,
        new_refresh_token=new_refresh_token,
        user_id=user_id,
        new_expires_at=new_expiry,
    )

    if not rotated:
        raise unauthorized()

    access_token, _ = AuthSecurity.create_access_token(
        user_id
    )

    set_refresh_cookie(response, new_refresh_token)

    return AuthResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_MINUTES * 60,
        user=UserResponse(
            id=user["id"],
            email=user["email"],
        ),
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout and revoke the refresh session",
)
def logout(
    request: Request,
    response: Response,
) -> MessageResponse:
    refresh_token = request.cookies.get(
        REFRESH_COOKIE_NAME
    )

    if refresh_token:
        auth_database.revoke_session(refresh_token)

    clear_refresh_cookie(response)

    return MessageResponse(
        message="Logged out successfully."
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
def get_my_profile(
    current_user: dict = Depends(get_current_user),
) -> UserResponse:
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
    )
