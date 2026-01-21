from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, SQLModel # Added SQLModel import

from ..db import get_session
from ..lib.jwt import create_access_token
from ..models.user import User
from ..services.user_service import UserService

router = APIRouter()

from pydantic import Field, validator

class UserCreate(SQLModel):
    email: str
    password: str = Field(..., max_length=72) # Added max_length for initial validation

    @validator("password")
    def password_length(cls, v):
        # Passlib (bcrypt) has a 72-byte limit for passwords.
        # Ensure that the password, when encoded to UTF-8, does not exceed this limit.
        if len(v.encode('utf-8')) > 72:
            raise ValueError("Password cannot be longer than 72 bytes")
        return v

@router.post("/signup", response_model=dict)
def register_user(
    user_data: UserCreate, user_service: Annotated[UserService, Depends()]
):
    try:
        user_service.create_user(user_data.email, user_data.password)
        return {"message": "User created successfully"}
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/login", response_model=dict)
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_service: Annotated[UserService, Depends()]
):
    user = user_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}
