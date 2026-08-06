"""Authentication endpoints: register and login."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateEmailError, InvalidCredentialsError
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserRead

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=201)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    repo = UserRepository(db)
    if repo.get_by_email(payload.email) is not None:
        raise DuplicateEmailError("An account with this email already exists")

    user = repo.create(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
    )
    logger.info("user registered user_id=%s", user.id)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    repo = UserRepository(db)
    user = repo.get_by_email(payload.email)

    if user is None or not verify_password(payload.password, user.hashed_password):
        logger.warning("failed login attempt email=%s", payload.email)
        raise InvalidCredentialsError("Incorrect email or password")

    token = create_access_token(subject=user.id)
    logger.info("user logged in user_id=%s", user.id)
    return Token(access_token=token)
