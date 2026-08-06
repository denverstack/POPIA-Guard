"""Shared FastAPI dependencies."""

from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import InvalidCredentialsError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

settings = get_settings()

# tokenUrl is used only to populate the Swagger "Authorize" flow — login
# itself accepts a JSON body, not an OAuth2 form, so this is documentation
# metadata rather than a strict OAuth2 implementation.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    user_id = decode_access_token(token)
    if user_id is None:
        raise InvalidCredentialsError("Invalid or expired token")

    user = UserRepository(db).get_by_id(user_id)
    if user is None or not user.is_active:
        raise InvalidCredentialsError("User not found or inactive")

    return user
