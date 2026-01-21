from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from ..db import get_session
from ..lib.jwt import verify_access_token
from ..models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/login")

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: Annotated[Session, Depends(get_session)]) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    user_id = verify_access_token(token, credentials_exception)
    user = session.get(User, user_id)
    if user is None:
        raise credentials_exception
    return user
